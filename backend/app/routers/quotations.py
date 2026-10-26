import json
import csv
import io
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from typing import List, Optional
from app.database import get_db
from app.models import QuotationCreate, QuotationResponse, QuotationItemResponse, VendorResponse
from app.services.compliance_service import audit_compliance
from app.services.cost_service import compute_tco

router = APIRouter(tags=["Quotations & Vendors"])

@router.get("/api/vendors", response_model=List[VendorResponse])
def list_vendors():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vendors ORDER BY rating DESC;")
        rows = cursor.fetchall()
        return [
            VendorResponse(
                id=r["id"],
                name=r["name"],
                code=r["code"],
                contact_email=r["contact_email"],
                country=r["country"],
                rating=r["rating"],
                tier=r["tier"],
                esg_score=r["esg_score"],
                iso_certs=json.loads(r["iso_certs"]) if r["iso_certs"] else [],
                historical_on_time_rate=r["historical_on_time_rate"]
            ) for r in rows
        ]

@router.get("/api/quotations", response_model=List[QuotationResponse])
def list_quotations(request_id: Optional[str] = Query(None)):
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
        SELECT q.*, v.name as vendor_name, v.code as vendor_code
        FROM quotations q
        LEFT JOIN vendors v ON q.vendor_id = v.id
        """
        params = []
        if request_id:
            query += " WHERE q.request_id = ?"
            params.append(request_id)
        query += " ORDER BY q.uploaded_at DESC;"
        
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        result = []
        for r in rows:
            quote_id = r["id"]
            cursor.execute("SELECT * FROM quotation_items WHERE quotation_id = ?;", (quote_id,))
            item_rows = cursor.fetchall()
            items = [
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
                ) for it in item_rows
            ]

            hidden_fee = float(r["hidden_fee"]) if "hidden_fee" in r.keys() else 0.0
            tco_calc = compute_tco(
                base_quote_amount=r["total_quote_amount"],
                shipping_fee=r["shipping_fee"],
                tax_amount=r["tax_amount"],
                quote_lead_time=r["lead_time_days"],
                rfq_deadline=21,
                quote_warranty_months=r["warranty_months"],
                rfq_min_warranty=24,
                hidden_fee=hidden_fee
            )

            result.append(
                QuotationResponse(
                    id=r["id"],
                    request_id=r["request_id"],
                    vendor_id=r["vendor_id"],
                    vendor_name=r["vendor_name"],
                    vendor_code=r["vendor_code"],
                    quote_reference=r["quote_reference"],
                    currency=r["currency"],
                    total_quote_amount=r["total_quote_amount"],
                    shipping_fee=r["shipping_fee"],
                    tax_amount=r["tax_amount"],
                    hidden_fee=hidden_fee,
                    landed_cost=tco_calc["landed_cost"],
                    lead_time_days=r["lead_time_days"],
                    warranty_months=r["warranty_months"],
                    payment_terms=r["payment_terms"],
                    compliance_status=r["compliance_status"],
                    compliance_notes=json.loads(r["compliance_notes"]) if r["compliance_notes"] else [],
                    uploaded_at=r["uploaded_at"],
                    raw_filename=r["raw_filename"],
                    items=items
                )
            )
        return result

@router.post("/api/quotations", response_model=QuotationResponse)
def create_quotation(payload: QuotationCreate):
    quote_id = f"QUOTE-{uuid.uuid4().hex[:8].upper()}"
    now_str = datetime.now(timezone.utc).isoformat()
    base_total = sum(it.quoted_unit_price * it.quantity for it in payload.items)

    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify RFQ and Vendor exist
        cursor.execute("SELECT * FROM rfq_requests WHERE id = ?;", (payload.request_id,))
        rfq_row = cursor.fetchone()
        if not rfq_row:
            raise HTTPException(status_code=404, detail="RFQ Request not found")
        rfq_dict = dict(rfq_row)
        rfq_dict["required_iso_certs"] = json.loads(rfq_row["required_iso_certs"]) if rfq_row["required_iso_certs"] else []

        cursor.execute("SELECT * FROM vendors WHERE id = ?;", (payload.vendor_id,))
        vendor_row = cursor.fetchone()
        if not vendor_row:
            raise HTTPException(status_code=404, detail="Vendor not found")
        vendor_dict = dict(vendor_row)
        vendor_dict["iso_certs"] = json.loads(vendor_row["iso_certs"]) if vendor_row["iso_certs"] else []

        # Audit compliance
        q_dict = {
            "warranty_months": payload.warranty_months,
            "lead_time_days": payload.lead_time_days,
            "payment_terms": payload.payment_terms,
            "hidden_fee": payload.hidden_fee
        }
        audit = audit_compliance(vendor_dict, q_dict, rfq_dict)
        compliance_status = "VERIFIED" if audit["passed"] and payload.hidden_fee == 0 else "WARNING"
        compliance_notes = audit["issues"] + audit["warnings"]

        cursor.execute("""
        INSERT INTO quotations (
            id, request_id, vendor_id, quote_reference, currency,
            total_quote_amount, shipping_fee, tax_amount, hidden_fee, lead_time_days,
            warranty_months, payment_terms, compliance_status, compliance_notes,
            uploaded_at, raw_filename
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            quote_id, payload.request_id, payload.vendor_id, payload.quote_reference, payload.currency,
            base_total, payload.shipping_fee, payload.tax_amount, payload.hidden_fee, payload.lead_time_days,
            payload.warranty_months, payload.payment_terms, compliance_status,
            json.dumps(compliance_notes), now_str, "manual_entry.json"
        ))

        items_resp = []
        for it in payload.items:
            q_itm_id = f"QITM-{uuid.uuid4().hex[:8].upper()}"
            line_tot = round(it.quoted_unit_price * it.quantity, 2)
            cursor.execute("""
            INSERT INTO quotation_items (
                id, quotation_id, rfq_item_id, item_sku, description,
                quoted_unit_price, quantity, line_total, lead_time_days, compliance_flag
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                q_itm_id, quote_id, None, it.item_sku, it.description,
                it.quoted_unit_price, it.quantity, line_tot, it.lead_time_days, 1
            ))
            items_resp.append(
                QuotationItemResponse(
                    id=q_itm_id,
                    quotation_id=quote_id,
                    item_sku=it.item_sku,
                    description=it.description,
                    quoted_unit_price=it.quoted_unit_price,
                    quantity=it.quantity,
                    line_total=line_tot,
                    lead_time_days=it.lead_time_days,
                    compliance_flag=True
                )
            )

    tco_calc = compute_tco(
        base_quote_amount=base_total,
        shipping_fee=payload.shipping_fee,
        tax_amount=payload.tax_amount,
        quote_lead_time=payload.lead_time_days,
        rfq_deadline=rfq_dict["deadline_days"],
        quote_warranty_months=payload.warranty_months,
        rfq_min_warranty=rfq_dict["min_warranty_months"],
        hidden_fee=payload.hidden_fee
    )

    return QuotationResponse(
        id=quote_id,
        request_id=payload.request_id,
        vendor_id=payload.vendor_id,
        vendor_name=vendor_dict["name"],
        vendor_code=vendor_dict["code"],
        quote_reference=payload.quote_reference,
        currency=payload.currency,
        total_quote_amount=base_total,
        shipping_fee=payload.shipping_fee,
        tax_amount=payload.tax_amount,
        hidden_fee=payload.hidden_fee,
        landed_cost=tco_calc["landed_cost"],
        lead_time_days=payload.lead_time_days,
        warranty_months=payload.warranty_months,
        payment_terms=payload.payment_terms,
        compliance_status=compliance_status,
        compliance_notes=compliance_notes,
        uploaded_at=now_str,
        raw_filename="manual_entry.json",
        items=items_resp
    )

@router.post("/api/quotations/upload", response_model=QuotationResponse)
async def upload_quotation(
    request_id: str = Form(...),
    vendor_id: str = Form(...),
    quote_reference: str = Form(...),
    warranty_months: int = Form(24),
    lead_time_days: int = Form(14),
    shipping_fee: float = Form(1500.0),
    tax_amount: float = Form(4500.0),
    hidden_fee: float = Form(0.0),
    payment_terms: str = Form("Net 30"),
    file: UploadFile = File(...)
):
    """
    Parses an uploaded quotation file (CSV or JSON).
    Deterministic normalization of line items without requiring OCR or external tools.
    """
    contents = await file.read()
    filename = file.filename or "uploaded_quotation"
    items_to_add = []

    if filename.endswith(".json") or file.content_type == "application/json":
        try:
            data = json.loads(contents.decode("utf-8"))
            if isinstance(data, dict) and "items" in data:
                items_list = data["items"]
            elif isinstance(data, list):
                items_list = data
            else:
                items_list = []
            
            for it in items_list:
                items_to_add.append({
                    "sku": str(it.get("sku") or it.get("item_sku") or "CUSTOM-SKU"),
                    "description": str(it.get("description") or "Item Description"),
                    "unit_price": float(it.get("unit_price") or it.get("quoted_unit_price") or 0.0),
                    "quantity": int(it.get("quantity") or 1),
                    "lead_time": int(it.get("lead_time") or it.get("lead_time_days") or lead_time_days)
                })
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse JSON file: {str(e)}")
    else:
        # Default parse as CSV
        try:
            text = contents.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                lower_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                sku = lower_row.get("sku") or lower_row.get("item_sku") or "CUSTOM-SKU"
                desc = lower_row.get("description") or lower_row.get("item") or "Item Description"
                unit_price = float(lower_row.get("unit_price") or lower_row.get("price") or 0.0)
                qty = int(lower_row.get("quantity") or lower_row.get("qty") or 1)
                item_lt = int(lower_row.get("lead_time_days") or lower_row.get("lead_time") or lead_time_days)
                items_to_add.append({
                    "sku": sku,
                    "description": desc,
                    "unit_price": unit_price,
                    "quantity": qty,
                    "lead_time": item_lt
                })
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {str(e)}")

    if not items_to_add:
        items_to_add.append({
            "sku": "PARSED-ITEM-1",
            "description": f"Standard Deliverable from {filename}",
            "unit_price": 50000.0,
            "quantity": 1,
            "lead_time": lead_time_days
        })

    payload = QuotationCreate(
        request_id=request_id,
        vendor_id=vendor_id,
        quote_reference=quote_reference,
        shipping_fee=shipping_fee,
        tax_amount=tax_amount,
        hidden_fee=hidden_fee,
        lead_time_days=lead_time_days,
        warranty_months=warranty_months,
        payment_terms=payment_terms,
        items=[
            {
                "item_sku": it["sku"],
                "description": it["description"],
                "quoted_unit_price": it["unit_price"],
                "quantity": it["quantity"],
                "lead_time_days": it["lead_time"]
            } for it in items_to_add
        ]
    )

    resp = create_quotation(payload)
    resp.raw_filename = filename
    return resp

@router.post("/api/quotations/load-sample", response_model=QuotationResponse)
def load_sample_quotation(request_id: str = Query(...), vendor_id: str = Query(...)):
    """
    1-click helper to load a realistic supplier quotation for testing without files.
    """
    sample_items = [
        {"item_sku": "SRV-AI-800", "description": "High-Density AI Inference Server Rack Unit", "quoted_unit_price": 15400.0, "quantity": 4, "lead_time_days": 14},
        {"item_sku": "SW-NET-400G", "description": "400GbE Spine-Leaf Enterprise Switch 32-Port", "quoted_unit_price": 7900.0, "quantity": 2, "lead_time_days": 14},
        {"item_sku": "UPS-MOD-10K", "description": "10kVA Modular Online Double-Conversion Rack UPS", "quoted_unit_price": 2980.0, "quantity": 4, "lead_time_days": 10},
        {"item_sku": "CAB-FBR-OM4", "description": "Low-Latency Optical Fiber MPO Interconnect Bundles", "quoted_unit_price": 400.0, "quantity": 20, "lead_time_days": 7}
    ]
    ref_code = f"SMP-{vendor_id[-3:]}-{Date_timestamp()}"
    payload = QuotationCreate(
        request_id=request_id,
        vendor_id=vendor_id,
        quote_reference=ref_code,
        shipping_fee=1600.0,
        tax_amount=4800.0,
        hidden_fee=0.0,
        lead_time_days=14,
        warranty_months=36,
        payment_terms="Net 30",
        items=sample_items
    )
    return create_quotation(payload)

def Date_timestamp():
    return str(int(datetime.now().timestamp()))[-4:]
