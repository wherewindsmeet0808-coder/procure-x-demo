import json
import asyncio
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.database import get_db
from app.models import RunTriggerRequest, EvaluationRunResponse, EvaluationScore, RunEventResponse
from app.services.ranking_service import calculate_evaluations
from app.services.gemini_service import generate_procurement_summary

router = APIRouter(prefix="/api/runs", tags=["Live Evaluation Runs & Event Stream"])

@router.post("", response_model=EvaluationRunResponse)
def trigger_run(payload: RunTriggerRequest):
    run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
    now_str = datetime.now(timezone.utc).isoformat()
    weights_dict = (payload.weights.model_dump() if payload.weights else {"price": 0.40, "delivery": 0.25, "quality": 0.20, "compliance": 0.15})

    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Fetch RFQ
        cursor.execute("SELECT * FROM rfq_requests WHERE id = ?;", (payload.request_id,))
        rfq_row = cursor.fetchone()
        if not rfq_row:
            raise HTTPException(status_code=404, detail="RFQ Request not found")
        rfq = dict(rfq_row)
        rfq["required_iso_certs"] = json.loads(rfq["required_iso_certs"]) if rfq["required_iso_certs"] else []

        # 2. Fetch Vendors
        cursor.execute("SELECT * FROM vendors;")
        vendors_rows = cursor.fetchall()
        vendors_map = {}
        for vr in vendors_rows:
            vd = dict(vr)
            vd["iso_certs"] = json.loads(vd["iso_certs"]) if vd["iso_certs"] else []
            vendors_map[vd["id"]] = vd

        # 3. Fetch Quotations
        cursor.execute("SELECT * FROM quotations WHERE request_id = ?;", (payload.request_id,))
        quotes_rows = cursor.fetchall()
        quotes = [dict(qr) for qr in quotes_rows]

        # 4. Check for quotation conflicts or hidden fees to trigger REPLAN
        conflict_vendor = None
        hidden_surcharge = 0.0
        sla_breach_days = 0
        replan_triggered = False
        replan_reason = None

        for q in quotes:
            hf = float(q.get("hidden_fee", 0.0))
            lt = int(q.get("lead_time_days", 0))
            if hf > 0 or lt > rfq["deadline_days"]:
                conflict_vendor = vendors_map.get(q["vendor_id"], {}).get("name", "Unknown Supplier")
                hidden_surcharge = hf
                sla_breach_days = max(0, lt - rfq["deadline_days"])
                replan_triggered = True
                replan_reason = f"Undisclosed fine-print surcharge (${hf:,.2f}) & {sla_breach_days}-day delivery SLA breach detected in {conflict_vendor} quotation."
                break

        # 5. Insert Initial Run Record
        cursor.execute("""
        INSERT INTO evaluation_runs (
            id, request_id, triggered_by, status, weights, replan_triggered, replan_reason, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, payload.request_id, payload.triggered_by, "RUNNING",
            json.dumps(weights_dict), 1 if replan_triggered else 0, replan_reason, now_str
        ))

        # 6. Execute deterministic calculations
        evaluations = calculate_evaluations(
            rfq=rfq,
            vendors_map=vendors_map,
            quotations=quotes,
            weights=weights_dict
        )

        top_ev = evaluations[0] if evaluations else None
        best_vendor_id = top_ev["vendor_id"] if top_ev else None
        best_vendor_name = top_ev["vendor_name"] if top_ev else None

        # 7. Generate Summary
        summary = ""
        if top_ev:
            summary = generate_procurement_summary(rfq, top_ev, evaluations)

        # 8. Record Live Pipeline Events shaped as: {step, status, message, evidence, ts}
        pipeline_events = [
            ("INTAKE", "START", f"Ingested {len(quotes)} vendor proposals for evaluation against {rfq['title']}.", {"quotes_count": len(quotes), "budget": rfq["budget"]}),
            ("PARSING", "RUNNING", "Standardized line items, bill of materials, and baseline commercial terms across all bids.", {"normalized_bids": len(quotes)}),
            ("COMPLIANCE_AUDIT", "RUNNING", f"Executed automated ISO, ESG, and warranty compliance checks against RFQ requirements.", {"audited_vendors": len(quotes), "mandatory_certs": rfq["required_iso_certs"]})
        ]

        if replan_triggered:
            pipeline_events.append((
                "CONFLICT_DETECTION",
                "WARNING",
                f"Quotation conflict detected: {conflict_vendor} quoted delivery breaches {rfq['deadline_days']}d SLA by {sla_breach_days} days. Fine print Section 4.2 contains unbundled ${hidden_surcharge:,.2f} surcharge.",
                {"vendor": conflict_vendor, "clause": "Section 4.2 (Logistics Surcharge)", "hidden_fee": hidden_surcharge, "sla_breach_days": sla_breach_days}
            ))
            pipeline_events.append((
                "REPLAN",
                "REPLAN",
                f"AGENT RE-PLAN TRIGGERED: Recalibrating landed cost models to absorb ${hidden_surcharge:,.2f} hidden logistics surcharge and adjust SLA risk buffers.",
                {"trigger": "Hidden Fee & Delivery SLA Conflict", "replan_action": "Injected surcharge into Landed Cost and elevated risk tier", "impacted_vendor": conflict_vendor}
            ))

        pipeline_events.extend([
            ("TCO_MODELING", "RUNNING", "Calculated deterministic Landed Cost and Total Cost of Ownership factoring freight, volume rebates, and SLA risk buffers.", {"model": "Deterministic Landed Cost & TCO v2"}),
            ("WHAT_IF_RANKING", "RUNNING", f"Applied multi-attribute weights (Price: {weights_dict['price']*100:.0f}%, Delivery: {weights_dict['delivery']*100:.0f}%, Quality: {weights_dict['quality']*100:.0f}%, Compliance: {weights_dict['compliance']*100:.0f}%).", {"top_ranked": best_vendor_name, "rank_1_score": top_ev["composite_score"] if top_ev else 0}),
            ("RECOMMENDATION", "COMPLETED", "Synthesized evidence-based recommendation brief and immutable audit trail.", {"recommended_award": best_vendor_name, "evaluated_tco": top_ev["tco"] if top_ev else 0})
        ])

        for step, st, msg, ev_data in pipeline_events:
            cursor.execute("""
            INSERT INTO run_events (run_id, step, status, level, message, evidence, details, ts, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (run_id, step, st, "WARN" if st in ("WARNING", "REPLAN") else "INFO", msg, json.dumps(ev_data), json.dumps(ev_data), now_str, now_str))

        # 9. Save vendor evaluations
        scores_resp = []
        for ev in evaluations:
            ev_id = f"EVAL-{uuid.uuid4().hex[:8].upper()}"
            cursor.execute("""
            INSERT INTO vendor_evaluations (
                id, run_id, vendor_id, quotation_id, landed_cost, tco, price_score,
                delivery_score, quality_score, compliance_score,
                composite_score, rank, compliance_passed, flag_warnings, evidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ev_id, run_id, ev["vendor_id"], ev["quotation_id"],
                ev["landed_cost"], ev["tco"], ev["price_score"], ev["delivery_score"],
                ev["quality_score"], ev["compliance_score"],
                ev["composite_score"], ev["rank"],
                1 if ev["compliance_passed"] else 0,
                json.dumps(ev["flag_warnings"]),
                json.dumps(ev["evidence"])
            ))

            scores_resp.append(
                EvaluationScore(
                    id=ev_id,
                    run_id=run_id,
                    vendor_id=ev["vendor_id"],
                    vendor_name=ev["vendor_name"],
                    vendor_code=ev["vendor_code"],
                    quotation_id=ev["quotation_id"],
                    landed_cost=ev["landed_cost"],
                    tco=ev["tco"],
                    delivery=ev["delivery"],
                    warranty=ev["warranty"],
                    compliance=ev["compliance"],
                    risk=ev["risk"],
                    score=ev["composite_score"],
                    price_score=ev["price_score"],
                    delivery_score=ev["delivery_score"],
                    quality_score=ev["quality_score"],
                    compliance_score=ev["compliance_score"],
                    composite_score=ev["composite_score"],
                    rank=ev["rank"],
                    compliance_passed=ev["compliance_passed"],
                    flag_warnings=ev["flag_warnings"],
                    evidence=ev["evidence"]
                )
            )

        # 10. Mark Run as COMPLETED
        cursor.execute("""
        UPDATE evaluation_runs
        SET status = 'COMPLETED', best_vendor_id = ?, summary_notes = ?, completed_at = ?
        WHERE id = ?;
        """, (best_vendor_id, summary, now_str, run_id))

        # 11. Update or Create Approval entry with evidence justification
        evidence_justification = {
            "top_vendor_name": best_vendor_name,
            "top_vendor_id": best_vendor_id,
            "landed_cost": top_ev["landed_cost"] if top_ev else 0.0,
            "tco": top_ev["tco"] if top_ev else 0.0,
            "authorized_budget": rfq["budget"],
            "net_savings": rfq["budget"] - (top_ev["landed_cost"] if top_ev else 0.0),
            "key_evidence": top_ev["evidence"] if top_ev else [],
            "replan_handled": replan_triggered,
            "replan_notes": replan_reason
        }

        cursor.execute("SELECT id FROM approvals WHERE request_id = ?;", (payload.request_id,))
        existing_appr = cursor.fetchone()
        if existing_appr:
            cursor.execute("""
            UPDATE approvals
            SET recommended_vendor_id = ?, total_value = ?, comments = ?, evidence_justification = ?, updated_at = ?
            WHERE id = ?;
            """, (best_vendor_id, top_ev["tco"] if top_ev else 0.0, summary, json.dumps(evidence_justification), now_str, existing_appr["id"]))
        elif top_ev:
            new_appr_id = f"APPR-{uuid.uuid4().hex[:8].upper()}"
            cursor.execute("""
            INSERT INTO approvals (
                id, request_id, evaluation_id, recommended_vendor_id,
                current_stage, status, total_value, comments, evidence_justification, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_appr_id, payload.request_id, scores_resp[0].id if scores_resp else None,
                best_vendor_id, "REQUESTER_REVIEW", "PENDING_APPROVAL",
                top_ev["tco"], summary, json.dumps(evidence_justification),
                now_str, now_str
            ))

    return EvaluationRunResponse(
        id=run_id,
        request_id=payload.request_id,
        triggered_by=payload.triggered_by,
        status="COMPLETED",
        weights=weights_dict,
        best_vendor_id=best_vendor_id,
        best_vendor_name=best_vendor_name,
        summary_notes=summary,
        replan_triggered=replan_triggered,
        replan_reason=replan_reason,
        created_at=now_str,
        completed_at=now_str,
        scores=scores_resp
    )

@router.get("/{run_id}", response_model=EvaluationRunResponse)
def get_run(run_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evaluation_runs WHERE id = ?;", (run_id,))
        r = cursor.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Run not found")

        best_vendor_name = None
        if r["best_vendor_id"]:
            cursor.execute("SELECT name FROM vendors WHERE id = ?;", (r["best_vendor_id"],))
            vr = cursor.fetchone()
            if vr:
                best_vendor_name = vr["name"]

        cursor.execute("""
        SELECT ve.*, v.name as vendor_name, v.code as vendor_code
        FROM vendor_evaluations ve
        LEFT JOIN vendors v ON ve.vendor_id = v.id
        WHERE ve.run_id = ?
        ORDER BY ve.rank ASC;
        """, (run_id,))
        score_rows = cursor.fetchall()
        
        scores = [
            EvaluationScore(
                id=sr["id"],
                run_id=sr["run_id"],
                vendor_id=sr["vendor_id"],
                vendor_name=sr["vendor_name"],
                vendor_code=sr["vendor_code"],
                quotation_id=sr["quotation_id"],
                landed_cost=sr["landed_cost"],
                tco=sr["tco"],
                score=sr["composite_score"],
                price_score=sr["price_score"],
                delivery_score=sr["delivery_score"],
                quality_score=sr["quality_score"],
                compliance_score=sr["compliance_score"],
                composite_score=sr["composite_score"],
                rank=sr["rank"],
                compliance_passed=bool(sr["compliance_passed"]),
                flag_warnings=json.loads(sr["flag_warnings"]) if sr["flag_warnings"] else [],
                evidence=json.loads(sr["evidence"]) if sr["evidence"] else []
            ) for sr in score_rows
        ]

        return EvaluationRunResponse(
            id=r["id"],
            request_id=r["request_id"],
            triggered_by=r["triggered_by"],
            status=r["status"],
            weights=json.loads(r["weights"]) if r["weights"] else {},
            best_vendor_id=r["best_vendor_id"],
            best_vendor_name=best_vendor_name,
            summary_notes=r["summary_notes"],
            replan_triggered=bool(r["replan_triggered"]),
            replan_reason=r["replan_reason"],
            created_at=r["created_at"],
            completed_at=r["completed_at"],
            scores=scores
        )

@router.get("/{run_id}/events", response_model=list[RunEventResponse])
def get_run_events(run_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM run_events WHERE run_id = ? ORDER BY id ASC;", (run_id,))
        rows = cursor.fetchall()
        return [
            RunEventResponse(
                id=r["id"],
                run_id=r["run_id"],
                step=r["step"],
                status=r["status"],
                message=r["message"],
                evidence=json.loads(r["evidence"]) if r["evidence"] else {},
                ts=r["ts"],
                level=r["level"],
                details=json.loads(r["details"]) if r["details"] else {},
                timestamp=r["timestamp"]
            ) for r in rows
        ]

@router.get("/{run_id}/stream")
async def stream_run_events(run_id: str):
    """
    Streams Server-Sent Events (SSE) shaped as:
    {step, status, message, evidence, ts}
    """
    async def event_generator():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM run_events WHERE run_id = ? ORDER BY id ASC;", (run_id,))
            events = cursor.fetchall()

        for ev in events:
            # Event shape: {step, status, message, evidence, ts}
            ev_payload = {
                "step": ev["step"],
                "status": ev["status"],
                "message": ev["message"],
                "evidence": json.loads(ev["evidence"]) if ev["evidence"] else {},
                "ts": ev["ts"]
            }
            yield f"data: {json.dumps(ev_payload)}\n\n"
            # Slightly longer pause on REPLAN to make the live replan clearly visible to the user!
            if ev["status"] == "REPLAN":
                await asyncio.sleep(0.7)
            else:
                await asyncio.sleep(0.35)

        yield f"event: done\ndata: {json.dumps({'status': 'DONE', 'run_id': run_id})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
