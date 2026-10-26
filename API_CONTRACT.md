# ProcureSense AI — API Contract Specification

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000`  
**Protocol:** HTTP/1.1 & Server-Sent Events (SSE)  
**Database:** SQLite (`procurement.db`)  
**Offline Deterministic Engine:** Enabled (Default)

---

## 1. System & Demo Control

### `GET /api/health`
Health check and environment status.
- **Response `200 OK`**:
  ```json
  {
    "status": "HEALTHY",
    "app_name": "ProcureSense AI",
    "version": "1.0.0",
    "demo_mode": true,
    "database": "SQLite (Connected)",
    "gemini_api_key_configured": false
  }
  ```

### `GET /api/demo/status`
Returns demo mode state, versioning, and whether running in offline heuristic mode or live Gemini API mode.
- **Response `200 OK`**:
  ```json
  {
    "demo_mode": true,
    "app_name": "ProcureSense AI",
    "version": "1.0.0",
    "gemini_enabled": false,
    "gemini_mode": "Offline Heuristic Deterministic Engine"
  }
  ```

### `POST /api/demo/seed`
Seeds realistic RFQs, vendors, line-item quotations, live evaluation runs, and approval records.
- **Response `200 OK`**:
  ```json
  {
    "status": "SUCCESS",
    "rfq_id": "RFQ-2026-088",
    "vendors_seeded": 4,
    "quotes_seeded": 4
  }
  ```

### `POST /api/demo/reset`
Drops all tables, recreates schema, and reseeds initial baseline state.

---

## 2. Procurement Requests (RFQs)

### `GET /api/requests`
List all procurement RFQs with their required specs, budgets, deadlines, and itemized lines.

### `GET /api/requests/{request_id}`
Get a single RFQ by ID.

### `POST /api/requests`
Create a new RFQ request.
- **Request Body**:
  ```json
  {
    "title": "Enterprise Edge Infrastructure & AI Server Fleet Upgrade",
    "department": "Cloud Infrastructure & AI Platforms",
    "category": "Hardware & Data Center",
    "budget": 150000.0,
    "currency": "USD",
    "deadline_days": 21,
    "min_warranty_months": 24,
    "min_esg_score": 70.0,
    "required_iso_certs": ["ISO-9001", "ISO-27001"],
    "items": [
      {
        "sku": "SRV-AI-800",
        "description": "8x GPU High-Density AI Inference Server",
        "quantity": 4,
        "target_unit_price": 16500.0,
        "specifications": {"cpus": "64-core", "gpus": "8x L40S"}
      }
    ]
  }
  ```
- **Response `200 OK`**: `RFQRequestResponse`

---

## 3. Vendors & Quotations

### `GET /api/vendors`
List registered vendors with ratings, tiers, ESG scores, ISO certificates, and historical on-time delivery rates.

### `GET /api/quotations?request_id={id}`
List submitted quotations for an RFQ, including line item pricing and compliance check notes.

### `POST /api/quotations`
Create a quotation directly via JSON payload.

### `POST /api/quotations/upload`
Upload a quotation file (CSV or JSON) via `multipart/form-data`.
- **Form Fields**:
  - `request_id`: string
  - `vendor_id`: string
  - `quote_reference`: string
  - `warranty_months`: int
  - `lead_time_days`: int
  - `shipping_fee`: float
  - `tax_amount`: float
  - `payment_terms`: string (e.g. "Net 30")
  - `file`: binary (CSV or JSON)
- **Supported CSV columns**: `sku`, `description`, `unit_price`, `quantity`, `lead_time`

---

## 4. Live Evaluation Runs & Event Stream

### `POST /api/runs`
Trigger evaluation run using deterministic multi-criteria scoring.
- **Request Body**:
  ```json
  {
    "request_id": "RFQ-2026-088",
    "triggered_by": "Strategic Procurement Specialist",
    "weights": {
      "price": 0.40,
      "delivery": 0.25,
      "quality": 0.20,
      "compliance": 0.15
    }
  }
  ```
- **Response `200 OK`**: `EvaluationRunResponse` with ranked scores and analytical summary.

### `GET /api/runs/{run_id}/events`
List all structured pipeline logs recorded during the run.

### `GET /api/runs/{run_id}/stream`
**Server-Sent Events (SSE)** endpoint. Streams live step-by-step evaluation updates:
1. `INTAKE`: Schema verification
2. `NORMALIZATION`: Currency and line item normalization
3. `COMPLIANCE_AUDIT`: ISO, ESG, warranty, and SLA verification
4. `TCO_MODELING`: Total Cost of Ownership calculation
5. `WHAT_IF_RANKING`: Multi-criteria weighted matrix execution
6. `SUMMARY_SYNTHESIS`: Executive recommendation generation

---

## 5. Vendor Comparison Matrix

### `GET /api/comparison/{request_id}`
Returns side-by-side comparative matrix of all competing vendors:
- Itemized pricing
- Deterministic Total Cost of Ownership (TCO) breakdown:
  - Base Direct Quote Amount
  - Freight & Shipping
  - Taxes
  - Volume Discounts
  - Risk-Adjusted Delivery Deficit Buffers
  - Supplemental Warranty Buffers
- Compliance Audit status and flags
- Budget savings percentage

---

## 6. What-If Sensitivity Ranking

### `POST /api/ranking/what-if`
Recalculates scores and ranks deterministically in real-time as sliders and filters adjust.
- **Request Body**:
  ```json
  {
    "request_id": "RFQ-2026-088",
    "weights": {
      "price": 0.50,
      "delivery": 0.20,
      "quality": 0.15,
      "compliance": 0.15
    },
    "max_budget_limit": 105000.0,
    "max_lead_time_days": 21,
    "min_warranty_months": 24
  }
  ```
- **Response `200 OK`**: Array of `EvaluationScore` sorted by Rank #1 to #N with disqualification flags.

---

## 7. Recommendation & Approval Workflow

### `GET /api/approvals/{request_id}`
Returns current approval state, stage, recommended award vendor, and immutable action audit log.

### `POST /api/approvals/{approval_id}/action`
Transitions workflow stage with audit trail.
- **Stages**: `REQUESTER_REVIEW` -> `PROCUREMENT_OFFICER_REVIEW` -> `FINANCE_DIRECTOR_REVIEW` -> `APPROVED`
- **Request Body**:
  ```json
  {
    "action": "APPROVE",
    "actor_name": "Elena Rostova",
    "role": "Finance Director",
    "notes": "Reviewed TCO variance against OPEX budget. Commercial terms approved."
  }
  ```

### `GET /api/approvals/{approval_id}/po`
Generates a structured, export-ready Purchase Order (PO) document with financial totals, terms, and item lines.
