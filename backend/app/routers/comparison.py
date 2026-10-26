import json
from fastapi import APIRouter, HTTPException
from app.database import get_db
from app.models import ComparisonMatrixResponse, VendorComparisonDetail, VendorResponse, QuotationResponse, QuotationItemResponse
from app.services.cost_service import compute_tco
from app.services.compliance_service import audit_compliance

router = APIRouter(prefix="/api/comparison", tags=["Vendor Comparison Matrix"])

@router.get("/{request_id}", response_model=ComparisonMatrixResponse)
def get_comparison_matrix(request_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Fetch RFQ
        cursor.execute("SELECT * FROM rfq_requests WHERE id = ?;", (request_id,))
        rfq_row = cursor.fetchone()
        if not rfq_row:
            raise HTTPException(status_code=404, detail="RFQ Request not found")
        rfq = dict(rfq_row)
        rfq["required_iso_certs"] = json.loads(rfq["required_iso_certs"]) if rfq["required_iso_certs"] else []

        # 2. Fetch Quotations with Vendors
        cursor.execute("""
        SELECT q.*, v.name as v_name, v.code as v_code, v.contact_email as v_email,
               v.country as v_country, v.rating as v_rating, v.tier as v_tier,
               v.esg_score as v_esg, v.iso_certs as v_iso, v.historical_on_time_rate as v_on_time
        FROM quotations q
        JOIN vendors v ON q.vendor_id = v.id
        WHERE q.request_id = ?;
        """, (request_id,))
        quotes_rows = cursor.fetchall()

        # Check latest run scores if available for composite score
        cursor.execute("SELECT id FROM evaluation_runs WHERE request_id = ? ORDER BY created_at DESC LIMIT 1;", (request_id,))
        latest_run = cursor.fetchone()
        run_scores_map = {}
        if latest_run:
            cursor.execute("SELECT vendor_id, composite_score FROM vendor_evaluations WHERE run_id = ?;", (latest_run["id"],))
            for sr in cursor.fetchall():
                run_scores_map[sr["vendor_id"]] = sr["composite_score"]

        vendors_compared = []
        for r in quotes_rows:
            v_obj = VendorResponse(
                id=r["vendor_id"],
                name=r["v_name"],
                code=r["v_code"],
                contact_email=r["v_email"],
                country=r["v_country"],
                rating=r["v_rating"],
                tier=r["v_tier"],
                esg_score=r["v_esg"],
                iso_certs=json.loads(r["v_iso"]) if r["v_iso"] else [],
                historical_on_time_rate=r["v_on_time"]
            )

            cursor.execute("SELECT * FROM quotation_items WHERE quotation_id = ?;", (r["id"],))
            it_rows = cursor.fetchall()
            q_items = [
                QuotationItemResponse(
                    id=it["id"],
                    quotation_id=it["quotation_id"],
                    item_sku=it["item_sku"],
                    description=it["description"],
                    quoted_unit_price=it["quoted_unit_price"],
                    quantity=it["quantity"],
                    line_total=it["line_total"],
                    lead_time_days=it["lead_time_days"],
                    compliance_flag=bool(it["compliance_flag"])
                ) for it in it_rows
            ]

            hidden_fee = float(r["hidden_fee"]) if "hidden_fee" in r.keys() else 0.0

            # Compute TCO breakdown
            tco_data = compute_tco(
                base_quote_amount=r["total_quote_amount"],
                shipping_fee=r["shipping_fee"],
                tax_amount=r["tax_amount"],
                quote_lead_time=r["lead_time_days"],
                rfq_deadline=rfq["deadline_days"],
                quote_warranty_months=r["warranty_months"],
                rfq_min_warranty=rfq["min_warranty_months"],
                hidden_fee=hidden_fee
            )

            q_obj = QuotationResponse(
                id=r["id"],
                request_id=r["request_id"],
                vendor_id=r["vendor_id"],
                vendor_name=r["v_name"],
                vendor_code=r["v_code"],
                quote_reference=r["quote_reference"],
                currency=r["currency"],
                total_quote_amount=r["total_quote_amount"],
                shipping_fee=r["shipping_fee"],
                tax_amount=r["tax_amount"],
                hidden_fee=hidden_fee,
                landed_cost=tco_data["landed_cost"],
                lead_time_days=r["lead_time_days"],
                warranty_months=r["warranty_months"],
                payment_terms=r["payment_terms"],
                compliance_status=r["compliance_status"],
                compliance_notes=json.loads(r["compliance_notes"]) if r["compliance_notes"] else [],
                uploaded_at=r["uploaded_at"],
                raw_filename=r["raw_filename"],
                items=q_items
            )

            # Audit compliance & risk
            audit = audit_compliance(v_obj.model_dump(), q_obj.model_dump(), rfq)

            lead_variance = r["lead_time_days"] - rfq["deadline_days"]
            budget_savings = ((rfq["budget"] - tco_data["landed_cost"]) / rfq["budget"] * 100.0) if rfq["budget"] > 0 else 0.0

            delivery_dim = {
                "quoted_days": r["lead_time_days"],
                "variance_days": lead_variance,
                "sla_passed": lead_variance <= 0,
                "on_time_rate": v_obj.historical_on_time_rate
            }

            warranty_dim = {
                "quoted_months": r["warranty_months"],
                "required_months": rfq["min_warranty_months"],
                "deficit_months": max(0, rfq["min_warranty_months"] - r["warranty_months"]),
                "passed": r["warranty_months"] >= rfq["min_warranty_months"]
            }

            compliance_dim = {
                "passed": audit["passed"],
                "score": audit["score"],
                "iso_certs": v_obj.iso_certs,
                "esg_score": v_obj.esg_score,
                "issues": audit["issues"],
                "warnings": audit["warnings"]
            }

            risk_dim = {
                "level": audit["risk_level"],
                "score": audit["risk_score"],
                "factors": audit["issues"] + audit["warnings"]
            }

            composite_score = run_scores_map.get(v_obj.id, round(audit["score"] * 0.9, 1))

            vendors_compared.append(
                VendorComparisonDetail(
                    vendor=v_obj,
                    quotation=q_obj,
                    landed_cost=tco_data["landed_cost"],
                    delivery=delivery_dim,
                    warranty=warranty_dim,
                    compliance=compliance_dim,
                    risk=risk_dim,
                    score=composite_score,
                    evidence=audit["evidence"],
                    tco=tco_data["total_tco"],
                    tco_breakdown=tco_data,
                    compliance_passed=audit["passed"],
                    compliance_issues=audit["issues"] + audit["warnings"],
                    lead_time_variance_days=lead_variance,
                    unit_price_savings_pct=round(budget_savings, 2)
                )
            )

        # Sort by Landed Cost ascending
        vendors_compared.sort(key=lambda x: x.landed_cost)

        return ComparisonMatrixResponse(
            request_id=request_id,
            rfq_title=rfq["title"],
            rfq_budget=rfq["budget"],
            vendors_compared=vendors_compared
        )
