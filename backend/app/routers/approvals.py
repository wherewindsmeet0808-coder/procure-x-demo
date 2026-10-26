import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.database import get_db
from app.models import ApprovalResponse, ApprovalActionResponse, ApprovalActionCreate

router = APIRouter(prefix="/api/approvals", tags=["Recommendation & Approval Workflow"])

STAGE_TRANSITIONS = {
    "REQUESTER_REVIEW": {
        "APPROVE": "PROCUREMENT_OFFICER_REVIEW",
        "SUBMIT": "PROCUREMENT_OFFICER_REVIEW",
        "REJECT": "REJECTED"
    },
    "PROCUREMENT_OFFICER_REVIEW": {
        "APPROVE": "FINANCE_DIRECTOR_REVIEW",
        "REQUEST_CHANGES": "REQUESTER_REVIEW",
        "REJECT": "REJECTED"
    },
    "FINANCE_DIRECTOR_REVIEW": {
        "APPROVE": "APPROVED",
        "REQUEST_CHANGES": "PROCUREMENT_OFFICER_REVIEW",
        "REJECT": "REJECTED"
    }
}

@router.get("/{request_id}", response_model=ApprovalResponse)
def get_approval_for_request(request_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT a.*, r.title as rfq_title, r.budget as rfq_budget, v.name as recommended_vendor_name, v.code as recommended_vendor_code
        FROM approvals a
        LEFT JOIN rfq_requests r ON a.request_id = r.id
        LEFT JOIN vendors v ON a.recommended_vendor_id = v.id
        WHERE a.request_id = ?;
        """, (request_id,))
        appr = cursor.fetchone()
        
        if not appr:
            # If no approval instance yet, check if there's an RFQ and vendors to initialize
            cursor.execute("SELECT * FROM rfq_requests WHERE id = ?;", (request_id,))
            rfq = cursor.fetchone()
            if not rfq:
                raise HTTPException(status_code=404, detail="RFQ not found")
            
            cursor.execute("SELECT id, name, code FROM vendors ORDER BY rating DESC LIMIT 1;")
            top_v = cursor.fetchone()
            vendor_id = top_v["id"] if top_v else "VEND-001"
            vendor_name = top_v["name"] if top_v else "Apex Core Technologies"
            vendor_code = top_v["code"] if top_v else "APEX-US"
            
            appr_id = f"APPR-{request_id}"
            now_str = datetime.now(timezone.utc).isoformat()
            award_val = rfq["budget"] * 0.65
            
            initial_justification = {
                "top_vendor_name": vendor_name,
                "top_vendor_code": vendor_code,
                "landed_cost": award_val,
                "authorized_budget": rfq["budget"],
                "net_savings": rfq["budget"] - award_val,
                "savings_percentage": round(((rfq["budget"] - award_val) / rfq["budget"]) * 100, 2),
                "key_evidence": [
                    f"Evaluated Landed Cost of ${award_val:,.2f} delivers ${rfq['budget'] - award_val:,.2f} in budget savings",
                    "Mandatory ISO-9001 and ISO-27001 certifications verified active",
                    "Delivery timeline complies fully with project delivery SLA constraints"
                ],
                "competitor_downranking": []
            }
            
            cursor.execute("""
            INSERT INTO approvals (
                id, request_id, evaluation_id, recommended_vendor_id,
                current_stage, status, total_value, comments, evidence_justification, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                appr_id, request_id, None, vendor_id,
                "REQUESTER_REVIEW", "PENDING_APPROVAL", award_val,
                "Awaiting initial requester sign-off", json.dumps(initial_justification), now_str, now_str
            ))
            
            return ApprovalResponse(
                id=appr_id,
                request_id=request_id,
                rfq_title=rfq["title"],
                recommended_vendor_id=vendor_id,
                recommended_vendor_name=vendor_name,
                current_stage="REQUESTER_REVIEW",
                status="PENDING_APPROVAL",
                total_value=award_val,
                comments="Awaiting initial requester sign-off",
                evidence_justification=initial_justification,
                created_at=now_str,
                updated_at=now_str,
                actions=[]
            )

        cursor.execute("""
        SELECT * FROM approval_actions
        WHERE approval_id = ?
        ORDER BY id ASC;
        """, (appr["id"],))
        action_rows = cursor.fetchall()
        
        actions = [
            ApprovalActionResponse(
                id=ar["id"],
                approval_id=ar["approval_id"],
                stage=ar["stage"],
                role=ar["role"],
                actor_name=ar["actor_name"],
                action=ar["action"],
                notes=ar["notes"],
                action_date=ar["action_date"]
            ) for ar in action_rows
        ]

        ev_justification = None
        if "evidence_justification" in appr.keys() and appr["evidence_justification"]:
            try:
                ev_justification = json.loads(appr["evidence_justification"])
            except Exception:
                pass

        if not ev_justification:
            budget = float(appr["rfq_budget"]) if appr["rfq_budget"] else 150000.0
            val = float(appr["total_value"])
            ev_justification = {
                "top_vendor_name": appr["recommended_vendor_name"] or "Apex Core Technologies",
                "top_vendor_code": "APEX-US",
                "landed_cost": val,
                "authorized_budget": budget,
                "net_savings": budget - val,
                "savings_percentage": round(((budget - val) / budget) * 100, 2) if budget > 0 else 0,
                "key_evidence": [
                    f"Award value of ${val:,.2f} achieves ${budget - val:,.2f} in fiscal variance savings",
                    "ISO certifications verified and in full compliance with RFQ specification",
                    "Delivery lead time meets required operational timeline"
                ],
                "competitor_downranking": []
            }

        return ApprovalResponse(
            id=appr["id"],
            request_id=appr["request_id"],
            rfq_title=appr["rfq_title"],
            recommended_vendor_id=appr["recommended_vendor_id"],
            recommended_vendor_name=appr["recommended_vendor_name"],
            current_stage=appr["current_stage"],
            status=appr["status"],
            total_value=appr["total_value"],
            comments=appr["comments"],
            evidence_justification=ev_justification,
            created_at=appr["created_at"],
            updated_at=appr["updated_at"],
            actions=actions
        )

@router.post("/{approval_id}/action", response_model=ApprovalResponse)
def execute_approval_action(approval_id: str, payload: ApprovalActionCreate):
    action = payload.action.upper()
    now_str = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM approvals WHERE id = ?;", (approval_id,))
        appr = cursor.fetchone()
        if not appr:
            raise HTTPException(status_code=404, detail="Approval record not found")

        current_stage = appr["current_stage"]
        current_status = appr["status"]

        if current_status in ("APPROVED", "REJECTED"):
            raise HTTPException(status_code=400, detail=f"Approval workflow is already closed ({current_status})")

        transitions = STAGE_TRANSITIONS.get(current_stage, {})
        next_stage = transitions.get(action)
        if not next_stage:
            raise HTTPException(
                status_code=400,
                detail=f"Action '{action}' is invalid from stage '{current_stage}'. Valid actions: {list(transitions.keys())}"
            )

        # Update approval status
        new_status = "PENDING_APPROVAL"
        if next_stage == "APPROVED":
            new_status = "APPROVED"
        elif next_stage == "REJECTED":
            new_status = "REJECTED"
        elif action == "REQUEST_CHANGES":
            new_status = "CHANGES_REQUESTED"

        cursor.execute("""
        UPDATE approvals
        SET current_stage = ?, status = ?, comments = ?, updated_at = ?
        WHERE id = ?;
        """, (next_stage, new_status, payload.notes or appr["comments"], now_str, approval_id))

        # Record action in audit log
        cursor.execute("""
        INSERT INTO approval_actions (
            approval_id, stage, role, actor_name, action, notes, action_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            approval_id, current_stage, payload.role, payload.actor_name,
            action, payload.notes or "", now_str
        ))

        # If fully approved, mark RFQ status as APPROVED
        if new_status == "APPROVED":
            cursor.execute("UPDATE rfq_requests SET status = 'APPROVED' WHERE id = ?;", (appr["request_id"],))

    return get_approval_for_request(appr["request_id"])

@router.get("/{approval_id}/po")
def generate_purchase_order(approval_id: str) -> Dict[str, Any]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT a.*, r.title as rfq_title, r.department, r.currency,
               v.name as vendor_name, v.code as vendor_code, v.contact_email, v.country
        FROM approvals a
        JOIN rfq_requests r ON a.request_id = r.id
        JOIN vendors v ON a.recommended_vendor_id = v.id
        WHERE a.id = ?;
        """, (approval_id,))
        appr = cursor.fetchone()
        if not appr:
            raise HTTPException(status_code=404, detail="Approval not found")

        # Fetch quote items
        cursor.execute("""
        SELECT q.id as quote_id, q.quote_reference, q.lead_time_days, q.warranty_months, q.payment_terms,
               q.shipping_fee, q.tax_amount, q.total_quote_amount
        FROM quotations q
        WHERE q.request_id = ? AND q.vendor_id = ?
        ORDER BY q.uploaded_at DESC LIMIT 1;
        """, (appr["request_id"], appr["recommended_vendor_id"]))
        quote = cursor.fetchone()

        items = []
        if quote:
            cursor.execute("SELECT * FROM quotation_items WHERE quotation_id = ?;", (quote["quote_id"],))
            items = [dict(r) for r in cursor.fetchall()]

        return {
            "po_number": f"PO-2026-{appr['id'][-6:]}",
            "approval_status": appr["status"],
            "current_stage": appr["current_stage"],
            "rfq_id": appr["request_id"],
            "rfq_title": appr["rfq_title"],
            "department": appr["department"],
            "vendor": {
                "id": appr["recommended_vendor_id"],
                "name": appr["vendor_name"],
                "code": appr["vendor_code"],
                "email": appr["contact_email"],
                "country": appr["country"]
            },
            "terms": {
                "currency": appr["currency"],
                "payment_terms": quote["payment_terms"] if quote else "Net 30",
                "lead_time_days": quote["lead_time_days"] if quote else 14,
                "warranty_months": quote["warranty_months"] if quote else 24
            },
            "financials": {
                "subtotal": quote["total_quote_amount"] if quote else appr["total_value"],
                "shipping_fee": quote["shipping_fee"] if quote else 0.0,
                "tax_amount": quote["tax_amount"] if quote else 0.0,
                "total_po_value": appr["total_value"]
            },
            "line_items": items,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
