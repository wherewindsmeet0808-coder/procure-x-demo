import json
from fastapi import APIRouter, HTTPException
from typing import List
from app.database import get_db
from app.models import WhatIfRequest, EvaluationScore
from app.services.ranking_service import calculate_evaluations

router = APIRouter(prefix="/api/ranking", tags=["What-If Sensitivity Ranking"])

@router.post("/what-if", response_model=List[EvaluationScore])
def calculate_what_if_ranking(payload: WhatIfRequest):
    """
    Recalculates ranking dynamically based on weights and constraints
    WITHOUT re-extracting or re-parsing quotation documents.
    """
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

        # 3. Fetch Quotations (already ingested in DB)
        cursor.execute("SELECT * FROM quotations WHERE request_id = ?;", (payload.request_id,))
        quotes_rows = cursor.fetchall()
        quotes = [dict(qr) for qr in quotes_rows]

        # 4. Instant deterministic recalculation
        evaluations = calculate_evaluations(
            rfq=rfq,
            vendors_map=vendors_map,
            quotations=quotes,
            weights=payload.weights.model_dump(),
            max_budget_limit=payload.max_budget_limit,
            max_lead_time_days=payload.max_lead_time_days,
            min_warranty_months=payload.min_warranty_months
        )

        return [
            EvaluationScore(
                id=f"WHATIF-{ev['vendor_id']}",
                run_id="DYNAMIC",
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
            ) for ev in evaluations
        ]
