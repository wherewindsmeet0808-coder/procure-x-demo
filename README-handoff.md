# PROCURE‑X Demo – Hand‑off Summary

- **What it is**: A complete procurement‑process demo (React + Vite + TypeScript front‑end, FastAPI back‑end, SQLite storage) that works **offline**.
- **How to start**:
  ```powershell
  cd <project‑root>
  .\run-dev.bat
  ```
  Backend runs on **http://127.0.0.1:8000**, frontend on **http://127.0.0.1:5173**.
- **Seed data**: Initialized by `backend/app/seed_data.py` (1 RFQ, 4 vendors, deterministic quotations). No external services are required.
- **API contract**: OpenAPI spec available at `backend/app/openapi.json` or at `http://127.0.0.1:8000/openapi.json` when running.
- **Runtime requirements**:
  - Python 3.12
  - PNPM (Node 18+) – the batch file installs it if missing.
- **Demo flow (8 stages)**:
  1️⃣ DEMO_MODE – seeded data
  2️⃣ New request creation & quotation upload
  3️⃣ Live run with SSE events `{step, status, message, evidence, ts}`
  4️⃣ REPLAN detection (hidden fee / SLA breach)
  5️⃣ Vendor comparison matrix (cost, delivery, warranty, compliance, risk, score, evidence)
  6️⃣ What‑If ranking controls (no re‑extraction)
  7️⃣ Recommendation screen with evidence‑based justification
  8️⃣ Human approval + audit trail

Feel free to explore the code, run `pytest backend/tests/test_direct.py`, or extend the UI.
