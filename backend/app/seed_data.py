import json
from datetime import datetime, timezone
from app.database import get_db, reset_db

def seed_demo_data():
    reset_db()
    
    now_str = datetime.now(timezone.utc).isoformat()
    
    rfq_id = "RFQ-2026-088"
    rfq_title = "Enterprise Edge Infrastructure & AI Server Fleet Upgrade"
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Insert RFQ Request (1 Request)
        cursor.execute("""
        INSERT INTO rfq_requests (
            id, title, department, category, budget, currency,
            deadline_days, min_warranty_months, min_esg_score,
            required_iso_certs, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rfq_id,
            rfq_title,
            "Cloud Infrastructure & AI Platforms",
            "Hardware & Data Center",
            150000.0,
            "USD",
            21,
            24,
            70.0,
            json.dumps(["ISO-9001", "ISO-27001"]),
            "EVALUATED",
            now_str
        ))
        
        # 2. Insert RFQ Line Items
        rfq_items = [
            ("ITEM-1", rfq_id, "SRV-AI-800", "8x GPU High-Density AI Inference Server Rack Unit", 4, 16500.0, {"cpus": "64-core", "ram": "512GB", "gpus": "8x L40S"}),
            ("ITEM-2", rfq_id, "SW-NET-400G", "400GbE Spine-Leaf Enterprise Switch 32-Port", 2, 8500.0, {"ports": 32, "throughput": "12.8Tbps"}),
            ("ITEM-3", rfq_id, "UPS-MOD-10K", "10kVA Modular Online Double-Conversion Rack UPS", 4, 3200.0, {"capacity": "10kVA", "hot_swappable": True}),
            ("ITEM-4", rfq_id, "CAB-FBR-OM4", "Low-Latency Optical Fiber MPO Interconnect Bundles 100m", 20, 450.0, {"standard": "OM4", "length": "100m"})
        ]
        for it in rfq_items:
            cursor.execute("""
            INSERT INTO rfq_items (id, request_id, sku, description, quantity, target_unit_price, specifications)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (it[0], it[1], it[2], it[3], it[4], it[5], json.dumps(it[6])))

        # 3. Insert Four Competing Vendors (4 Vendors)
        vendors = [
            ("VEND-001", "Apex Core Technologies", "APEX-US", "procurement@apexcore.com", "United States", 4.85, "Tier-1", 88.0, ["ISO-9001", "ISO-27001", "ISO-14001"], 98.5),
            ("VEND-002", "GlobalSys Direct Corp", "GSYS-TW", "sales@globalsys-direct.tw", "Taiwan", 4.50, "Tier-1", 78.5, ["ISO-9001", "ISO-27001"], 94.0),
            ("VEND-003", "Horizon Hardware & Logistics", "HRZN-DE", "b2b@horizon-systems.de", "Germany", 4.10, "Tier-2", 72.0, ["ISO-9001"], 86.5),
            ("VEND-004", "EcoNet Cloud Systems", "ECON-SE", "nordic-deals@econet.se", "Sweden", 4.65, "Tier-2", 95.0, ["ISO-9001", "ISO-14001", "ISO-27001"], 92.0)
        ]
        for v in vendors:
            cursor.execute("""
            INSERT INTO vendors (id, name, code, contact_email, country, rating, tier, esg_score, iso_certs, historical_on_time_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7], json.dumps(v[8]), v[9]))

        # 4. Insert Quotations & Quotation Line Items
        quotes_data = [
            {
                "id": "QUOTE-001",
                "vendor_id": "VEND-001",
                "ref": "APX-2026-Q4-019",
                "lead_time": 14,
                "warranty": 36,
                "shipping": 1800.0,
                "tax": 5200.0,
                "hidden_fee": 0.0,
                "terms": "Net 30",
                "items": [
                    ("SRV-AI-800", "8x GPU High-Density AI Server", 15800.0, 4, 14),
                    ("SW-NET-400G", "400GbE Spine-Leaf Switch", 8100.0, 2, 14),
                    ("UPS-MOD-10K", "10kVA Modular Online UPS", 3050.0, 4, 10),
                    ("CAB-FBR-OM4", "OM4 Optical Fiber Bundles", 410.0, 20, 7)
                ]
            },
            {
                "id": "QUOTE-002",
                "vendor_id": "VEND-002",
                "ref": "GSD-ASIA-8821",
                "lead_time": 18,
                "warranty": 24,
                "shipping": 2600.0,
                "tax": 4800.0,
                "hidden_fee": 0.0,
                "terms": "Net 30",
                "items": [
                    ("SRV-AI-800", "8x GPU High-Density AI Server", 14900.0, 4, 18),
                    ("SW-NET-400G", "400GbE Spine-Leaf Switch", 7600.0, 2, 16),
                    ("UPS-MOD-10K", "10kVA Modular Online UPS", 2950.0, 4, 12),
                    ("CAB-FBR-OM4", "OM4 Optical Fiber Bundles", 380.0, 20, 10)
                ]
            },
            {
                "id": "QUOTE-003",
                "vendor_id": "VEND-003",
                "ref": "HZN-EU-44091",
                "lead_time": 26, # Exceeds 21d deadline by 5 days (SLA conflict)
                "warranty": 12, # Deficient warranty
                "shipping": 3100.0,
                "tax": 4500.0,
                "hidden_fee": 3500.0, # Hidden logistics fee in Section 4.2!
                "terms": "Net 45",
                "items": [
                    ("SRV-AI-800", "8x GPU High-Density AI Server", 15200.0, 4, 26),
                    ("SW-NET-400G", "400GbE Spine-Leaf Switch", 7900.0, 2, 22),
                    ("UPS-MOD-10K", "10kVA Modular Online UPS", 3100.0, 4, 18),
                    ("CAB-FBR-OM4", "OM4 Optical Fiber Bundles", 395.0, 20, 14)
                ]
            },
            {
                "id": "QUOTE-004",
                "vendor_id": "VEND-004",
                "ref": "ECO-NORD-092",
                "lead_time": 20,
                "warranty": 36,
                "shipping": 1950.0,
                "tax": 5400.0,
                "hidden_fee": 0.0,
                "terms": "Net 60",
                "items": [
                    ("SRV-AI-800", "Eco-Optimized 8x GPU AI Server", 16100.0, 4, 20),
                    ("SW-NET-400G", "Energy-Efficient 400GbE Switch", 8300.0, 2, 18),
                    ("UPS-MOD-10K", "High-Efficiency Modular UPS", 3150.0, 4, 14),
                    ("CAB-FBR-OM4", "Halogen-Free OM4 Fiber Cable", 430.0, 20, 10)
                ]
            }
        ]

        for q in quotes_data:
            base_total = sum(it[2] * it[3] for it in q["items"])
            cursor.execute("""
            INSERT INTO quotations (
                id, request_id, vendor_id, quote_reference, currency,
                total_quote_amount, shipping_fee, tax_amount, hidden_fee, lead_time_days,
                warranty_months, payment_terms, compliance_status, compliance_notes,
                uploaded_at, raw_filename
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                q["id"], rfq_id, q["vendor_id"], q["ref"], "USD",
                base_total, q["shipping"], q["tax"], q["hidden_fee"], q["lead_time"],
                q["warranty"], q["terms"], "VERIFIED" if q["hidden_fee"] == 0 else "WARNING",
                json.dumps(["Unbundled $3,500 logistics surcharge in Section 4.2", "Quoted lead time breaches 21-day SLA by 5 days"] if q["hidden_fee"] > 0 else []),
                now_str, f"{q['ref'].lower()}.json"
            ))

            for it in q["items"]:
                line_total = it[2] * it[3]
                item_id = f"QITM-{q['id']}-{it[0]}"
                cursor.execute("""
                INSERT INTO quotation_items (
                    id, quotation_id, rfq_item_id, item_sku, description,
                    quoted_unit_price, quantity, line_total, lead_time_days, compliance_flag
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item_id, q["id"], None, it[0], it[1], it[2], it[3], line_total, it[4], 1
                ))

        # 5. Insert Evaluation Run with visible REPLAN event
        run_id = "RUN-DEMO-001"
        cursor.execute("""
        INSERT INTO evaluation_runs (
            id, request_id, triggered_by, status, weights, best_vendor_id,
            summary_notes, replan_triggered, replan_reason, created_at, completed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, rfq_id, "Senior Procurement Specialist", "COMPLETED",
            json.dumps({"price": 0.40, "delivery": 0.25, "quality": 0.20, "compliance": 0.15}),
            "VEND-001",
            "Apex Core Technologies achieves the leading composite index score (96.7/100).",
            1,
            "Hidden $3,500 fuel/customs surcharge and 5-day delivery SLA breach detected in Horizon Hardware quotation (HZN-EU-44091).",
            now_str, now_str
        ))

        # 6. Insert live run events shaped as: {step, status, message, evidence, ts}
        events = [
            ("INTAKE", "START", "INFO", "Initiating quotation intake and schema verification for RFQ-2026-088", {"quotes_found": 4}, now_str),
            ("PARSING", "RUNNING", "INFO", "Line-item normalization completed across 4 vendor proposals (16 total items)", {"normalized": 16}, now_str),
            ("COMPLIANCE_AUDIT", "RUNNING", "INFO", "Audited ISO-9001 and ISO-27001 certifications against master registry", {"passed": 3, "warnings": 1}, now_str),
            ("CONFLICT_DETECTION", "WARNING", "WARN", "Quotation conflict detected: Horizon Hardware (VEND-003) delivery of 26 days breaches 21-day SLA by 5 days. Fine print Section 4.2 contains unbundled $3,500 surcharge.", {"vendor": "Horizon Hardware & Logistics", "clause": "Section 4.2", "hidden_fee": 3500.0, "sla_breach_days": 5}, now_str),
            ("REPLAN", "REPLAN", "WARN", "AGENT RE-PLAN TRIGGERED: Recalibrating landed cost models and risk penalties to absorb $3,500 undisclosed logistics surcharge into Horizon Hardware assessment.", {"trigger": "Hidden Fee & SLA Conflict", "penalty_adjustment": 3500.0, "risk_tier_shift": "Elevated to HIGH"}, now_str),
            ("TCO_MODELING", "RUNNING", "INFO", "Executed deterministic Total Cost of Ownership and Landed Cost calculations factoring freight, volume rebates, and risk buffers", {"model": "LandedCost-TCO-v2"}, now_str),
            ("WHAT_IF_RANKING", "RUNNING", "INFO", "Applied multi-attribute weights (Price: 40%, Delivery: 25%, Quality: 20%, Compliance: 15%). Apex Core Technologies ranked #1.", {"top_vendor": "VEND-001", "score": 96.7}, now_str),
            ("RECOMMENDATION", "COMPLETED", "INFO", "Synthesized evidence-based recommendation brief and audit trail.", {"recommended_award": "Apex Core Technologies", "variance_savings": "$53,130"}, now_str)
        ]
        for ev in events:
            cursor.execute("""
            INSERT INTO run_events (run_id, step, status, level, message, evidence, details, ts, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (run_id, ev[0], ev[1], ev[2], ev[3], json.dumps(ev[4]), json.dumps(ev[4]), ev[5], ev[5]))

        # 7. Insert pre-calculated vendor evaluations
        eval_records = [
            ("EVAL-001", run_id, "VEND-001", "QUOTE-001", 96870.0, 96870.0, 93.2, 98.5, 97.9, 100.0, 96.7, 1, 1, [], ["ISO-9001 and ISO-27001 verified", "Zero hidden surcharges", "98.5% on-time SLA history"]),
            ("EVAL-002", run_id, "VEND-002", "QUOTE-002", 90280.0, 90280.0, 100.0, 94.0, 93.0, 95.0, 96.4, 2, 1, [], ["Lowest base landed cost ($90,280)", "18-day lead time", "ISO-9001, ISO-27001"]),
            ("EVAL-004", run_id, "VEND-004", "QUOTE-004", 100140.0, 100140.0, 90.1, 92.0, 95.1, 100.0, 93.1, 3, 1, [], ["Highest ESG rating (95.0)", "ISO-14001, 9001, 27001", "Net 60 terms"]),
            ("EVAL-003", run_id, "VEND-003", "QUOTE-003", 103040.0, 99540.0, 87.2, 65.8, 87.4, 45.0, 73.5, 4, 0, ["Missing mandatory certification: ISO-27001", "Delivery exceeds 21-day SLA by 5 days", "Unbundled $3,500 fuel/customs surcharge"], ["Section 4.2 unbundled $3,500 fee detected during audit", "5-day delivery SLA breach", "12-month warranty deficit"])
        ]
        for er in eval_records:
            cursor.execute("""
            INSERT INTO vendor_evaluations (
                id, run_id, vendor_id, quotation_id, landed_cost, tco, price_score,
                delivery_score, quality_score, compliance_score,
                composite_score, rank, compliance_passed, flag_warnings, evidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                er[0], er[1], er[2], er[3], er[4], er[5], er[6], er[7], er[8], er[9], er[10], er[11], er[12], json.dumps(er[13]), json.dumps(er[14])
            ))

        # 8. Evidence-based justification payload for Approval
        evidence_justification = {
            "top_vendor_name": "Apex Core Technologies",
            "top_vendor_code": "APEX-US",
            "landed_cost": 96870.0,
            "authorized_budget": 150000.0,
            "net_savings": 53130.0,
            "savings_percentage": 35.42,
            "key_evidence": [
                "Landed Cost of $96,870 provides $53,130 (35.4%) in authorized fiscal budget savings",
                "Full compliance verification: ISO-9001, ISO-27001, and ISO-14001 registered on file",
                "Quoted lead time of 14 days delivers 7-day safety buffer before 21-day deadline",
                "36-month comprehensive warranty coverage exceeds 24-month minimum requirement by 12 months",
                "Zero hidden fee clauses; immune to replan adjustments that disqualified competitor bids"
            ],
            "competitor_downranking": [
                {"vendor": "GlobalSys Direct", "reason": "Rank #2: Slightly lower quality rating (4.50 vs 4.85) and longer delivery turnaround (18d vs 14d)."},
                {"vendor": "Horizon Hardware", "reason": "Rank #4: Disqualified / penalized due to unbundled $3,500 surcharge, 5-day SLA breach, and missing ISO-27001."},
                {"vendor": "EcoNet Systems", "reason": "Rank #3: Higher landed cost ($100,140) exceeding optimal price envelope."}
            ]
        }

        # 9. Insert Approval Instance
        approval_id = "APPR-2026-088"
        cursor.execute("""
        INSERT INTO approvals (
            id, request_id, evaluation_id, recommended_vendor_id,
            current_stage, status, total_value, comments, evidence_justification, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            approval_id, rfq_id, "EVAL-001", "VEND-001",
            "PROCUREMENT_OFFICER_REVIEW", "PENDING_APPROVAL", 96870.0,
            "Recommended for award to Apex Core Technologies based on highest overall compliance, zero hidden fees, and $53,130 budget savings.",
            json.dumps(evidence_justification),
            now_str, now_str
        ))

        # 10. Insert Approval Action Log
        cursor.execute("""
        INSERT INTO approval_actions (approval_id, stage, role, actor_name, action, notes, action_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            approval_id, "REQUESTER_REVIEW", "Lead Cloud Architect", "Sarah Lin",
            "APPROVE", "Technical specification evaluation completed. Endorsed Apex Core Technologies configuration.", now_str
        ))

    return {"status": "SUCCESS", "rfq_id": rfq_id, "vendors_seeded": 4, "quotes_seeded": 4}
