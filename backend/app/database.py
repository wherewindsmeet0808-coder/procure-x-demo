import sqlite3
import json
import os
from contextlib import contextmanager
from typing import Generator

DB_FILE = os.getenv("PROCUREMENT_DB_FILE", "procurement.db")

def get_db_path() -> str:
    d = os.path.dirname(DB_FILE)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    return DB_FILE

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Procurement Requests (RFQs)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS rfq_requests (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            department TEXT NOT NULL,
            category TEXT NOT NULL,
            budget REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            deadline_days INTEGER NOT NULL,
            min_warranty_months INTEGER NOT NULL DEFAULT 12,
            min_esg_score REAL NOT NULL DEFAULT 60.0,
            required_iso_certs TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'OPEN',
            created_at TEXT NOT NULL
        );
        """)

        # 2. Line Items in RFQ
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS rfq_items (
            id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL,
            sku TEXT NOT NULL,
            description TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            target_unit_price REAL NOT NULL,
            specifications TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY(request_id) REFERENCES rfq_requests(id) ON DELETE CASCADE
        );
        """)

        # 3. Vendors Master Directory
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            contact_email TEXT NOT NULL,
            country TEXT NOT NULL,
            rating REAL NOT NULL DEFAULT 4.0,
            tier TEXT NOT NULL DEFAULT 'Tier-1',
            esg_score REAL NOT NULL DEFAULT 75.0,
            iso_certs TEXT NOT NULL DEFAULT '[]',
            historical_on_time_rate REAL NOT NULL DEFAULT 95.0
        );
        """)

        # 4. Vendor Quotations
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotations (
            id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL,
            vendor_id TEXT NOT NULL,
            quote_reference TEXT NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            total_quote_amount REAL NOT NULL,
            shipping_fee REAL NOT NULL DEFAULT 0.0,
            tax_amount REAL NOT NULL DEFAULT 0.0,
            hidden_fee REAL NOT NULL DEFAULT 0.0,
            lead_time_days INTEGER NOT NULL,
            warranty_months INTEGER NOT NULL,
            payment_terms TEXT NOT NULL DEFAULT 'Net 30',
            compliance_status TEXT NOT NULL DEFAULT 'PENDING',
            compliance_notes TEXT NOT NULL DEFAULT '[]',
            uploaded_at TEXT NOT NULL,
            raw_filename TEXT,
            FOREIGN KEY(request_id) REFERENCES rfq_requests(id) ON DELETE CASCADE,
            FOREIGN KEY(vendor_id) REFERENCES vendors(id) ON DELETE CASCADE
        );
        """)

        # 5. Quotation Line Items
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotation_items (
            id TEXT PRIMARY KEY,
            quotation_id TEXT NOT NULL,
            rfq_item_id TEXT,
            item_sku TEXT NOT NULL,
            description TEXT NOT NULL,
            quoted_unit_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            line_total REAL NOT NULL,
            lead_time_days INTEGER NOT NULL,
            compliance_flag INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(quotation_id) REFERENCES quotations(id) ON DELETE CASCADE
        );
        """)

        # 6. Evaluation Runs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluation_runs (
            id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL,
            triggered_by TEXT NOT NULL DEFAULT 'System Analyst',
            status TEXT NOT NULL DEFAULT 'QUEUED',
            weights TEXT NOT NULL DEFAULT '{}',
            best_vendor_id TEXT,
            summary_notes TEXT,
            replan_triggered INTEGER NOT NULL DEFAULT 0,
            replan_reason TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY(request_id) REFERENCES rfq_requests(id) ON DELETE CASCADE
        );
        """)

        # 7. Live Run Events (SSE feed) shaped as: {step, status, message, evidence, ts}
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS run_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            step TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'RUNNING',
            level TEXT NOT NULL DEFAULT 'INFO',
            message TEXT NOT NULL,
            evidence TEXT NOT NULL DEFAULT '{}',
            details TEXT NOT NULL DEFAULT '{}',
            ts TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(run_id) REFERENCES evaluation_runs(id) ON DELETE CASCADE
        );
        """)

        # 8. Vendor Evaluation Scores (per run)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendor_evaluations (
            id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            vendor_id TEXT NOT NULL,
            quotation_id TEXT NOT NULL,
            landed_cost REAL NOT NULL DEFAULT 0.0,
            tco REAL NOT NULL,
            price_score REAL NOT NULL,
            delivery_score REAL NOT NULL,
            quality_score REAL NOT NULL,
            compliance_score REAL NOT NULL,
            composite_score REAL NOT NULL,
            rank INTEGER NOT NULL,
            compliance_passed INTEGER NOT NULL DEFAULT 1,
            flag_warnings TEXT NOT NULL DEFAULT '[]',
            evidence TEXT NOT NULL DEFAULT '[]',
            FOREIGN KEY(run_id) REFERENCES evaluation_runs(id) ON DELETE CASCADE,
            FOREIGN KEY(vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
            FOREIGN KEY(quotation_id) REFERENCES quotations(id) ON DELETE CASCADE
        );
        """)

        # 9. Approval Workflow Instances
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL,
            evaluation_id TEXT,
            recommended_vendor_id TEXT NOT NULL,
            current_stage TEXT NOT NULL DEFAULT 'REQUESTER_REVIEW',
            status TEXT NOT NULL DEFAULT 'IN_REVIEW',
            total_value REAL NOT NULL,
            comments TEXT NOT NULL DEFAULT '',
            evidence_justification TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(request_id) REFERENCES rfq_requests(id) ON DELETE CASCADE,
            FOREIGN KEY(recommended_vendor_id) REFERENCES vendors(id) ON DELETE CASCADE
        );
        """)

        # 10. Approval Action Logs (Audit Trail)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS approval_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            approval_id TEXT NOT NULL,
            stage TEXT NOT NULL,
            role TEXT NOT NULL,
            actor_name TEXT NOT NULL,
            action TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            action_date TEXT NOT NULL,
            FOREIGN KEY(approval_id) REFERENCES approvals(id) ON DELETE CASCADE
        );
        """)

def reset_db():
    with get_db() as conn:
        cursor = conn.cursor()
        tables = [
            "approval_actions", "approvals", "vendor_evaluations",
            "run_events", "evaluation_runs", "quotation_items",
            "quotations", "vendors", "rfq_items", "rfq_requests"
        ]
        for t in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {t};")
    init_db()
