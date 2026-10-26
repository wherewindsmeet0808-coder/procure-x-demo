import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from typing import List
from app.database import get_db
from app.models import RFQRequestCreate, RFQRequestResponse, RFQItemResponse

router = APIRouter(prefix="/api/requests", tags=["Procurement Requests (RFQs)"])

@router.get("", response_model=List[RFQRequestResponse])
def list_requests():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rfq_requests ORDER BY created_at DESC;")
        rows = cursor.fetchall()
        
        results = []
        for r in rows:
            req_id = r["id"]
            cursor.execute("SELECT * FROM rfq_items WHERE request_id = ?;", (req_id,))
            item_rows = cursor.fetchall()
            items = [
                RFQItemResponse(
                    id=it["id"],
                    request_id=it["request_id"],
                    sku=it["sku"],
                    description=it["description"],
                    quantity=it["quantity"],
                    target_unit_price=it["target_unit_price"],
                    specifications=json.loads(it["specifications"]) if it["specifications"] else {}
                ) for it in item_rows
            ]
            
            results.append(
                RFQRequestResponse(
                    id=r["id"],
                    title=r["title"],
                    department=r["department"],
                    category=r["category"],
                    budget=r["budget"],
                    currency=r["currency"],
                    deadline_days=r["deadline_days"],
                    min_warranty_months=r["min_warranty_months"],
                    min_esg_score=r["min_esg_score"],
                    required_iso_certs=json.loads(r["required_iso_certs"]) if r["required_iso_certs"] else [],
                    status=r["status"],
                    created_at=r["created_at"],
                    items=items
                )
            )
        return results

@router.get("/{request_id}", response_model=RFQRequestResponse)
def get_request(request_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rfq_requests WHERE id = ?;", (request_id,))
        r = cursor.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="RFQ Request not found")

        cursor.execute("SELECT * FROM rfq_items WHERE request_id = ?;", (request_id,))
        item_rows = cursor.fetchall()
        items = [
            RFQItemResponse(
                id=it["id"],
                request_id=it["request_id"],
                sku=it["sku"],
                description=it["description"],
                quantity=it["quantity"],
                target_unit_price=it["target_unit_price"],
                specifications=json.loads(it["specifications"]) if it["specifications"] else {}
            ) for it in item_rows
        ]

        return RFQRequestResponse(
            id=r["id"],
            title=r["title"],
            department=r["department"],
            category=r["category"],
            budget=r["budget"],
            currency=r["currency"],
            deadline_days=r["deadline_days"],
            min_warranty_months=r["min_warranty_months"],
            min_esg_score=r["min_esg_score"],
            required_iso_certs=json.loads(r["required_iso_certs"]) if r["required_iso_certs"] else [],
            status=r["status"],
            created_at=r["created_at"],
            items=items
        )

@router.post("", response_model=RFQRequestResponse)
def create_request(payload: RFQRequestCreate):
    req_id = f"RFQ-{int(datetime.now().timestamp())}"
    now_str = datetime.now(timezone.utc).isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO rfq_requests (
            id, title, department, category, budget, currency,
            deadline_days, min_warranty_months, min_esg_score,
            required_iso_certs, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            req_id,
            payload.title,
            payload.department,
            payload.category,
            payload.budget,
            payload.currency,
            payload.deadline_days,
            payload.min_warranty_months,
            payload.min_esg_score,
            json.dumps(payload.required_iso_certs),
            "OPEN",
            now_str
        ))
        
        items_resp = []
        for it in payload.items:
            item_id = f"ITEM-{uuid.uuid4().hex[:8]}"
            cursor.execute("""
            INSERT INTO rfq_items (id, request_id, sku, description, quantity, target_unit_price, specifications)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id, req_id, it.sku, it.description, it.quantity, it.target_unit_price,
                json.dumps(it.specifications or {})
            ))
            items_resp.append(
                RFQItemResponse(
                    id=item_id,
                    request_id=req_id,
                    sku=it.sku,
                    description=it.description,
                    quantity=it.quantity,
                    target_unit_price=it.target_unit_price,
                    specifications=it.specifications or {}
                )
            )

    return RFQRequestResponse(
        id=req_id,
        title=payload.title,
        department=payload.department,
        category=payload.category,
        budget=payload.budget,
        currency=payload.currency,
        deadline_days=payload.deadline_days,
        min_warranty_months=payload.min_warranty_months,
        min_esg_score=payload.min_esg_score,
        required_iso_certs=payload.required_iso_certs,
        status="OPEN",
        created_at=now_str,
        items=items_resp
    )

@router.delete("/{request_id}")
def delete_request(request_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rfq_requests WHERE id = ?;", (request_id,))
    return {"message": "RFQ deleted successfully"}
