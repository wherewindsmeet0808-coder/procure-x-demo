# ProcureSense AI — Autonomous Procurement Prototype

> **Enterprise Procurement Prototype** built as a unified mono-repository featuring **React + Vite + TypeScript**, **FastAPI**, **SQLite**, and **Server-Sent Events (SSE)**.  
> Operates **100% offline** with fully deterministic costing, compliance checks, and sensitivity ranking. Gemini AI integration is strictly optional.

---

## 🏛️ System Architecture

```
procurement-prototype/
├── backend/
│   ├── app/
│   │   ├── config.py             # Settings, DEMO_MODE, optional Gemini API key
│   │   ├── database.py           # SQLite connection, schema DDL, session manager
│   │   ├── models.py             # Pydantic schemas & DTOs
│   │   ├── seed_data.py          # Realistic baseline enterprise procurement seed
│   │   ├── main.py               # FastAPI application, CORS, router mounts
│   │   ├── services/
│   │   │   ├── cost_service.py       # Deterministic Total Cost of Ownership (TCO)
│   │   │   ├── compliance_service.py # Deterministic ISO, ESG, SLA & warranty audit
│   │   │   ├── ranking_service.py    # Deterministic multi-attribute sensitivity scoring
│   │   │   ├── gemini_service.py     # Deterministic heuristic brief (Gemini fallback)
│   │   └── routers/
│   │       ├── demo.py           # /api/demo/seed, /api/demo/reset, /api/demo/status
│   │       ├── requests.py       # /api/requests CRUD
│   │       ├── quotations.py     # /api/quotations, /api/vendors, /api/quotations/upload
│   │       ├── events.py         # /api/runs, /api/runs/{id}/stream (SSE)
│   │       ├── comparison.py     # /api/comparison/{request_id}
│   │       ├── ranking.py        # /api/ranking/what-if
│   │       └── approvals.py      # /api/approvals, /api/approvals/{id}/action, /po
│   └── tests/
│       └── test_direct.py        # Pytest test suite covering all services & routers
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx        # Top status bar, DEMO_MODE badge, reseed trigger
│   │   │   ├── StageNav.tsx      # Stage workflow navigation stepper
│   │   │   └── stages/
│   │   │       ├── RequestStage.tsx     # Stage 1: RFQ BOM & Specifications
│   │   │       ├── QuotationStage.tsx   # Stage 2: Quotation intake & CSV/JSON upload
│   │   │       ├── LiveRunStage.tsx     # Stage 3: Real-time SSE live event stream
│   │   │       ├── ComparisonStage.tsx  # Stage 4: Side-by-side vendor TCO matrix
│   │   │       ├── WhatIfStage.tsx      # Stage 5: What-If weight sliders & filters
│   │   │       └── ApprovalStage.tsx    # Stage 6: Approval state machine & PO export
│   │   ├── services/api.ts       # Typed API client
│   │   ├── types/procurement.ts  # TypeScript contracts
│   │   ├── App.tsx               # Root application coordinator
│   │   └── index.css             # Enterprise design system
│   ├── vite.config.ts            # Vite proxy & bundler configuration
│   └── package.json
├── API_CONTRACT.md               # Complete REST & SSE specification
├── run-dev.bat                   # 1-click concurrent Windows dev server runner
├── run-backend.bat               # Dedicated backend launcher (Port 8000)
├── run-frontend.bat              # Dedicated frontend launcher (Port 5173)
├── test-all.bat                  # Full verification suite (Pytest + Vite Build)
└── README.md
```

---

## 🔒 Deterministic Guarantees

Every cost calculation, compliance decision, and vendor ranking is mathematically reproducible with zero stochastic variance:

1. **Total Cost of Ownership (TCO)**:
   $$\text{TCO} = (\text{Base Items Direct} + \text{Freight} + \text{Taxes} - \text{Volume Discount}) + \text{SLA Delay Risk Buffer} + \text{Warranty Deficit Buffer}$$
   - **Volume Discount**: 2.5% rebate on base amount exceeding $\$100,000$; 1.5% for $\ge \$50,000$.
   - **SLA Delay Penalty**: $\$200/\text{day}$ for quoted delivery exceeding the authorized RFQ deadline.
   - **Warranty Deficit Buffer**: $\$250/\text{month}$ for coverage falling short of the mandatory RFQ warranty.

2. **Compliance Rules Audit**:
   - Mandatory ISO Certifications (e.g., ISO-9001, ISO-27001): missing certificates subtract 20 points and fail the audit.
   - Minimum ESG Score: vendors below threshold are flagged with critical warnings.
   - Delivery SLA & Payment Terms: verified against organization purchasing guidelines.

3. **Multi-Attribute Ranking Formula**:
   $$\text{Score} = w_{\text{price}} \cdot S_{\text{price}} + w_{\text{delivery}} \cdot S_{\text{delivery}} + w_{\text{quality}} \cdot S_{\text{quality}} + w_{\text{compliance}} \cdot S_{\text{compliance}}$$
   - Normalization: $S_{\text{price}} = 100 \times \frac{\min(\text{TCO})}{\text{TCO}_{\text{vendor}}}$
   - Ties broken deterministically by composite score, then lowest TCO, then vendor ID.

---

## 🌐 Offline First & Gemini Optionality

- **100% Offline by Default**: The entire prototype runs without an internet connection or external API keys.
- **Deterministic Heuristic Engine**: Automatically synthesizes structured executive briefs, ROI variance, and risk analyses without LLM calls.
- **Optional Gemini Integration**: If `GEMINI_API_KEY` is provided in the environment, the backend gracefully attempts generative enrichment and falls back seamlessly if offline or unauthenticated.

---

## 🎯 DEMO_MODE & Seeded Scenario

The system boots with `DEMO_MODE=true` by default and auto-populates a realistic enterprise procurement baseline:
- **Project**: `RFQ-2026-088` — *Enterprise Edge Infrastructure & AI Server Fleet Upgrade*
- **Department**: Cloud Infrastructure & AI Platforms
- **Budget**: $\$150,000$ USD (21-Day SLA, Min 24mo Warranty, Min ESG 70.0, ISO-9001, ISO-27001)
- **4 Competing Suppliers**:
  1. **Apex Core Technologies** (Tier-1, USA): Premium quality, fully certified, 14-day delivery ($96,870 TCO).
  2. **GlobalSys Direct Corp** (Tier-1, Taiwan): Aggressive unit pricing ($90,280 TCO), 18-day delivery.
  3. **Horizon Hardware & Logistics** (Tier-2, Germany): Quoted 26 days (breaches 21d SLA), 12mo warranty (deficit), missing ISO-27001.
  4. **EcoNet Cloud Systems** (Tier-2, Sweden): Top ESG score (95.0), high sustainability ($100,140 TCO).

You can reset the database to this baseline at any time with the **"Reset Demo"** button in the header or via `POST /api/demo/reset`.

---

## 🚀 Exact Local Commands to Run & Test

### Recommended Setup (Set Workspace)
Open this folder as your active workspace in Antigravity or VS Code:
```
C:\Users\ssant\.gemini\antigravity\scratch\procurement-prototype
```

### 1. Launch All Servers (1-Click Concurrent)
Double-click or run:
```cmd
.\run-dev.bat
```
*This opens dedicated terminal windows for the backend (`http://127.0.0.1:8000`) and frontend (`http://127.0.0.1:5173`).*

### 2. Run Individual Servers Manually

#### Backend (FastAPI + SQLite):
```powershell
$env:PATH = "C:\Users\ssant\.cache\codex-runtimes\codex-primary-runtime\dependencies\python;C:\Users\ssant\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Scripts;" + $env:PATH
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*API Swagger Documentation: `http://127.0.0.1:8000/docs`*

#### Frontend (React + Vite + TypeScript):
```powershell
$env:PATH = "C:\Users\ssant\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;C:\Users\ssant\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback;" + $env:PATH
cd frontend
pnpm run dev --host 127.0.0.1
```
*Web Dashboard: `http://127.0.0.1:5173`*

### 3. Run Automated Tests
To run the complete verification suite (backend pytest + frontend TypeScript typecheck/build):
```cmd
.\test-all.bat
```

Or run test suites independently:
```powershell
# Backend pytest
$env:PATH = "C:\Users\ssant\.cache\codex-runtimes\codex-primary-runtime\dependencies\python;C:\Users\ssant\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Scripts;" + $env:PATH
cd backend
python -m pytest tests/test_direct.py -v

# Frontend build & typecheck
$env:PATH = "C:\Users\ssant\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;C:\Users\ssant\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback;" + $env:PATH
cd frontend
pnpm run build
```

---

## 📋 Step-by-Step Stage Walkthrough

1. **Stage 1: RFQ Request**
   - Review active RFQ specifications, authorized budget, and line-item bill of materials.
   - Use the **"+ New RFQ"** button to create custom procurement packages.

2. **Stage 2: Quotation Upload**
   - Inspect vendor quotes and extracted line items.
   - Click **"Sample CSV"** to download a ready-to-use bid template, or upload your own CSV/JSON quote.

3. **Stage 3: Live Run Events**
   - Adjust run weights and click **"Execute Run"**.
   - Watch the animated 6-phase pipeline progress with real-time Server-Sent Events (SSE) streaming into the live terminal feed.

4. **Stage 4: Vendor Comparison Matrix**
   - Audit side-by-side breakdowns of Direct Cost vs TCO, volume discounts, freight, and risk buffers.
   - Review compliance badges and SLA variance flags.

5. **Stage 5: What-If Ranking & Sensitivity Analysis**
   - Drag real-time sliders for Price, Delivery, Quality, and Compliance.
   - Apply preset strategies (*Cost Minimizer*, *Urgent SLA*, *ESG Focused*) and scenario constraints (*Max Budget*, *Max Lead Time*, *Min Warranty*) to visualize instantaneous rank shifts.

6. **Stage 6: Recommendation & Approval Workflow**
   - Read the executive recommendation report with budget savings analysis.
   - Execute formal multi-stage sign-offs (*Requester Sign-Off* $\to$ *Procurement Officer Approval* $\to$ *Finance Director Approval*).
   - View the immutable audit trail and click **"Generate Purchase Order (PO)"** to review and print the official PO.
