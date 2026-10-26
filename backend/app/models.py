from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- RFQ Request Models ---
class RFQItemCreate(BaseModel):
    sku: str
    description: str
    quantity: int
    target_unit_price: float
    specifications: Optional[Dict[str, Any]] = Field(default_factory=dict)

class RFQItemResponse(RFQItemCreate):
    id: str
    request_id: str

class RFQRequestCreate(BaseModel):
    title: str
    department: str
    category: str
    budget: float
    currency: str = "USD"
    deadline_days: int
    min_warranty_months: int = 12
    min_esg_score: float = 60.0
    required_iso_certs: List[str] = Field(default_factory=list)
    items: List[RFQItemCreate] = Field(default_factory=list)

class RFQRequestResponse(BaseModel):
    id: str
    title: str
    department: str
    category: str
    budget: float
    currency: str
    deadline_days: int
    min_warranty_months: int
    min_esg_score: float
    required_iso_certs: List[str]
    status: str
    created_at: str
    items: List[RFQItemResponse] = Field(default_factory=list)

# --- Vendor Models ---
class VendorResponse(BaseModel):
    id: str
    name: str
    code: str
    contact_email: str
    country: str
    rating: float
    tier: str
    esg_score: float
    iso_certs: List[str]
    historical_on_time_rate: float

# --- Quotation Models ---
class QuotationItemCreate(BaseModel):
    item_sku: str
    description: str
    quoted_unit_price: float
    quantity: int
    lead_time_days: int

class QuotationItemResponse(QuotationItemCreate):
    id: str
    quotation_id: str
    line_total: float
    compliance_flag: bool

class QuotationCreate(BaseModel):
    request_id: str
    vendor_id: str
    quote_reference: str
    currency: str = "USD"
    shipping_fee: float = 0.0
    tax_amount: float = 0.0
    hidden_fee: float = 0.0
    lead_time_days: int
    warranty_months: int
    payment_terms: str = "Net 30"
    items: List[QuotationItemCreate]

class QuotationResponse(BaseModel):
    id: str
    request_id: str
    vendor_id: str
    vendor_name: Optional[str] = None
    vendor_code: Optional[str] = None
    quote_reference: str
    currency: str
    total_quote_amount: float
    shipping_fee: float
    tax_amount: float
    hidden_fee: float = 0.0
    landed_cost: Optional[float] = None
    lead_time_days: int
    warranty_months: int
    payment_terms: str
    compliance_status: str
    compliance_notes: List[str]
    uploaded_at: str
    raw_filename: Optional[str] = None
    items: List[QuotationItemResponse] = Field(default_factory=list)

# --- Live Run & SSE Event Models ---
class RankingWeights(BaseModel):
    price: float = 0.40
    delivery: float = 0.25
    quality: float = 0.20
    compliance: float = 0.15

class RunTriggerRequest(BaseModel):
    request_id: str
    triggered_by: str = "Procurement Specialist"
    weights: Optional[RankingWeights] = None

# SSE Event schema: {step, status, message, evidence, ts}
class RunEventResponse(BaseModel):
    id: Optional[int] = None
    run_id: Optional[str] = None
    step: str
    status: str = "RUNNING"
    message: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    ts: str
    # Compatibility fields
    level: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

class EvaluationScore(BaseModel):
    id: str
    run_id: str
    vendor_id: str
    vendor_name: str
    vendor_code: str
    quotation_id: str
    landed_cost: float = 0.0
    tco: float
    delivery: Optional[Dict[str, Any]] = None
    warranty: Optional[Dict[str, Any]] = None
    compliance: Optional[Dict[str, Any]] = None
    risk: Optional[Dict[str, Any]] = None
    score: float = 0.0
    price_score: float
    delivery_score: float
    quality_score: float
    compliance_score: float
    composite_score: float
    rank: int
    compliance_passed: bool
    flag_warnings: List[str]
    evidence: List[str] = Field(default_factory=list)

class EvaluationRunResponse(BaseModel):
    id: str
    request_id: str
    triggered_by: str
    status: str
    weights: Dict[str, float]
    best_vendor_id: Optional[str] = None
    best_vendor_name: Optional[str] = None
    summary_notes: Optional[str] = None
    replan_triggered: bool = False
    replan_reason: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    scores: List[EvaluationScore] = Field(default_factory=list)

# --- What-If Ranking Query ---
class WhatIfRequest(BaseModel):
    request_id: str
    weights: RankingWeights
    max_budget_limit: Optional[float] = None
    max_lead_time_days: Optional[int] = None
    min_warranty_months: Optional[int] = None

# --- Comparison Matrix Models ---
class VendorComparisonDetail(BaseModel):
    vendor: VendorResponse
    quotation: QuotationResponse
    landed_cost: float
    delivery: Dict[str, Any]
    warranty: Dict[str, Any]
    compliance: Dict[str, Any]
    risk: Dict[str, Any]
    score: float
    evidence: List[str]
    tco: float
    tco_breakdown: Dict[str, float]
    compliance_passed: bool
    compliance_issues: List[str]
    lead_time_variance_days: int
    unit_price_savings_pct: float

class ComparisonMatrixResponse(BaseModel):
    request_id: str
    rfq_title: str
    rfq_budget: float
    vendors_compared: List[VendorComparisonDetail]

# --- Approval Workflow Models ---
class ApprovalActionCreate(BaseModel):
    action: str  # "APPROVE", "REJECT", "REQUEST_CHANGES"
    actor_name: str
    role: str
    notes: Optional[str] = ""

class ApprovalActionResponse(BaseModel):
    id: int
    approval_id: str
    stage: str
    role: str
    actor_name: str
    action: str
    notes: str
    action_date: str

class ApprovalResponse(BaseModel):
    id: str
    request_id: str
    rfq_title: Optional[str] = None
    recommended_vendor_id: str
    recommended_vendor_name: Optional[str] = None
    current_stage: str
    status: str
    total_value: float
    comments: str
    evidence_justification: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str
    actions: List[ApprovalActionResponse] = Field(default_factory=list)
