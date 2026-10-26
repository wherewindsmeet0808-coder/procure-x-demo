import os
import json
import pytest

os.environ["PROCUREMENT_DB_FILE"] = "test_procurement.db"
os.environ["DEMO_MODE"] = "true"

from app.database import init_db, reset_db
from app.seed_data import seed_demo_data
from app.models import (
    RFQRequestCreate, RFQItemCreate, QuotationCreate, QuotationItemCreate,
    RunTriggerRequest, RankingWeights, WhatIfRequest, ApprovalActionCreate
)
from app.routers.demo import get_demo_status, seed_data, reset_data
from app.routers.requests import list_requests, get_request, create_request
from app.routers.quotations import list_vendors, list_quotations, create_quotation
from app.routers.events import trigger_run, get_run, get_run_events
from app.routers.comparison import get_comparison_matrix
from app.routers.ranking import calculate_what_if_ranking
from app.routers.approvals import get_approval_for_request, execute_approval_action, generate_purchase_order
from app.services.cost_service import compute_tco
from app.services.compliance_service import audit_compliance
from app.services.ranking_service import calculate_evaluations

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    seed_demo_data()
    yield

def test_demo_status_and_seed():
    status = get_demo_status()
    assert status["demo_mode"] is True
    assert status["app_name"] == "PROCURE-X"
    assert "Offline Heuristic" in status["gemini_mode"]
    
    reset_res = reset_data()
    assert "re-seeded" in reset_res["message"]

def test_rfq_crud():
    reqs = list_requests()
    assert len(reqs) == 1  # Exactly one seeded request for DEMO_MODE
    rfq_id = reqs[0].id
    
    single = get_request(rfq_id)
    assert single.id == rfq_id
    assert single.budget == 150000.0
    assert len(single.items) == 4

    new_rfq = create_request(RFQRequestCreate(
        title="Direct Test RFQ",
        department="Engineering",
        category="Compute",
        budget=80000.0,
        deadline_days=14,
        min_warranty_months=24,
        min_esg_score=70.0,
        required_iso_certs=["ISO-9001"],
        items=[
            RFQItemCreate(sku="TST-1", description="Test Server", quantity=2, target_unit_price=30000.0)
        ]
    ))
    assert new_rfq.title == "Direct Test RFQ"
    assert len(new_rfq.items) == 1

def test_deterministic_cost_and_compliance():
    # Test Landed Cost & TCO
    tco_res = compute_tco(
        base_quote_amount=100000.0,
        shipping_fee=2000.0,
        tax_amount=5000.0,
        quote_lead_time=25,
        rfq_deadline=21,
        quote_warranty_months=12,
        rfq_min_warranty=24,
        hidden_fee=3500.0
    )
    # base has 2.5% volume discount ($2500)
    # landed_cost: 100000 + 2000 + 5000 - 2500 + 3500 = 108000.0
    # delay penalty: 4 days * $200 = $800
    # warranty deficit: 12 months * $250 = $3000
    # total_tco: 108000 + 800 + 3000 = 111800.0
    assert tco_res["base_amount"] == 100000.0
    assert tco_res["hidden_fee"] == 3500.0
    assert tco_res["landed_cost"] == 108000.0
    assert tco_res["delay_days"] == 4
    assert tco_res["lead_time_risk_cost"] == 800.0
    assert tco_res["warranty_deficit_months"] == 12
    assert tco_res["warranty_risk_cost"] == 3000.0
    assert tco_res["total_tco"] == 111800.0

    # Test Compliance & Risk
    vendor_mock = {
        "id": "V-1",
        "name": "Test Vendor",
        "iso_certs": ["ISO-9001"],
        "esg_score": 65.0,
        "historical_on_time_rate": 88.0
    }
    rfq_mock = {
        "required_iso_certs": ["ISO-9001", "ISO-27001"],
        "min_esg_score": 70.0,
        "min_warranty_months": 24,
        "deadline_days": 21
    }
    quote_mock = {
        "warranty_months": 12,
        "lead_time_days": 25,
        "payment_terms": "Net 30",
        "hidden_fee": 3500.0
    }
    audit = audit_compliance(vendor_mock, quote_mock, rfq_mock)
    assert audit["passed"] is False
    assert audit["risk_level"] in ("MEDIUM", "HIGH")
    assert len(audit["evidence"]) >= 3
    assert any("ISO-27001" in issue for issue in audit["issues"])
    assert any("ESG score" in issue for issue in audit["issues"])

def test_quotations_and_vendor_endpoints():
    vendors = list_vendors()
    assert len(vendors) == 4  # Exactly four vendors in DEMO_MODE
    
    quotes = list_quotations(request_id="RFQ-2026-088")
    assert len(quotes) == 4
    
    # Test new quotation creation with hidden fee detection
    new_q = create_quotation(QuotationCreate(
        request_id="RFQ-2026-088",
        vendor_id="VEND-001",
        quote_reference="REF-UNIT-01",
        shipping_fee=1500.0,
        tax_amount=4000.0,
        hidden_fee=0.0,
        lead_time_days=12,
        warranty_months=36,
        payment_terms="Net 30",
        items=[
            QuotationItemCreate(
                item_sku="SRV-AI-800",
                description="8x GPU Server",
                quoted_unit_price=15000.0,
                quantity=4,
                lead_time_days=12
            )
        ]
    ))
    assert new_q.quote_reference == "REF-UNIT-01"
    assert new_q.total_quote_amount == 60000.0
    assert new_q.landed_cost is not None

def test_live_run_and_replan_event():
    # Trigger Run
    run_resp = trigger_run(RunTriggerRequest(
        request_id="RFQ-2026-088",
        triggered_by="Strategic AI Evaluator",
        weights=RankingWeights(price=0.40, delivery=0.25, quality=0.20, compliance=0.15)
    ))
    assert run_resp.status == "COMPLETED"
    assert run_resp.replan_triggered is True
    assert "surcharge" in run_resp.replan_reason.lower()
    assert len(run_resp.scores) == 4

    # Verify SSE events shape: {step, status, message, evidence, ts}
    events = get_run_events(run_resp.id)
    assert len(events) >= 7

    replan_events = [e for e in events if e.status == "REPLAN" or e.step == "REPLAN"]
    assert len(replan_events) >= 1
    replan_ev = replan_events[0]
    assert replan_ev.step == "REPLAN"
    assert replan_ev.status == "REPLAN"
    assert hasattr(replan_ev, "message") and replan_ev.message != ""
    assert hasattr(replan_ev, "evidence") and isinstance(replan_ev.evidence, dict)
    assert hasattr(replan_ev, "ts") and replan_ev.ts != ""

def test_vendor_comparison_with_seven_dimensions():
    # 5. Vendor comparison with calculated: landed cost, delivery, warranty, compliance, risk, score, and evidence
    matrix = get_comparison_matrix("RFQ-2026-088")
    assert matrix.rfq_budget == 150000.0
    assert len(matrix.vendors_compared) == 4

    for vc in matrix.vendors_compared:
        # 1. Landed Cost
        assert vc.landed_cost > 0
        # 2. Delivery
        assert "quoted_days" in vc.delivery
        assert "variance_days" in vc.delivery
        # 3. Warranty
        assert "quoted_months" in vc.warranty
        assert "passed" in vc.warranty
        # 4. Compliance
        assert "passed" in vc.compliance
        assert "iso_certs" in vc.compliance
        # 5. Risk
        assert vc.risk["level"] in ("LOW", "MEDIUM", "HIGH")
        assert "score" in vc.risk
        # 6. Score
        assert vc.score >= 0.0
        # 7. Evidence
        assert isinstance(vc.evidence, list) and len(vc.evidence) > 0

def test_what_if_controls_without_reextraction():
    # 6. What-if controls that recalculate ranking without re-extracting quotations
    # Dynamic recalculation test
    what_if_price = calculate_what_if_ranking(WhatIfRequest(
        request_id="RFQ-2026-088",
        weights=RankingWeights(price=0.90, delivery=0.04, quality=0.03, compliance=0.03)
    ))
    assert len(what_if_price) == 4
    assert what_if_price[0].rank == 1
    assert what_if_price[0].vendor_id == "VEND-002"  # Lowest price winner

    what_if_quality = calculate_what_if_ranking(WhatIfRequest(
        request_id="RFQ-2026-088",
        weights=RankingWeights(price=0.05, delivery=0.05, quality=0.50, compliance=0.40)
    ))
    assert what_if_quality[0].rank == 1
    assert what_if_quality[0].vendor_id == "VEND-001"  # Highest quality/compliance winner

def test_recommendation_and_approval_controls():
    # 7 & 8: Recommendation with evidence-based justification, human approval controls and audit trail
    appr = get_approval_for_request("RFQ-2026-088")
    assert appr.status == "PENDING_APPROVAL"
    assert appr.evidence_justification is not None
    assert "key_evidence" in appr.evidence_justification
    assert len(appr.evidence_justification["key_evidence"]) >= 3

    # Human approval transition: Requester -> Procurement Officer -> Finance Director -> APPROVED
    if appr.current_stage == "REQUESTER_REVIEW":
        appr = execute_approval_action(appr.id, ApprovalActionCreate(
            action="APPROVE",
            actor_name="Alex Tech Lead",
            role="Lead Cloud Architect",
            notes="Technical specs verified."
        ))

    appr = execute_approval_action(appr.id, ApprovalActionCreate(
        action="APPROVE",
        actor_name="Marcus Vance",
        role="Procurement Officer",
        notes="Commercial audit verified with replan adjustments."
    ))
    assert appr.current_stage == "FINANCE_DIRECTOR_REVIEW"

    appr = execute_approval_action(appr.id, ApprovalActionCreate(
        action="APPROVE",
        actor_name="Elena Rostova",
        role="Finance Director",
        notes="Fiscal OPEX allocation approved."
    ))
    assert appr.status == "APPROVED"
    assert len(appr.actions) >= 3

    po = generate_purchase_order(appr.id)
    assert po["approval_status"] == "APPROVED"
    assert len(po["line_items"]) >= 1
