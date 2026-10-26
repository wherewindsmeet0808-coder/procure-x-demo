export interface RFQItem {
  id: string
  request_id: string
  sku: string
  description: string
  quantity: number
  target_unit_price: number
  specifications: Record<string, any>
}

export interface RFQRequest {
  id: string
  title: string
  department: string
  category: string
  budget: number
  currency: string
  deadline_days: number
  min_warranty_months: number
  min_esg_score: number
  required_iso_certs: string[]
  status: string
  created_at: string
  items: RFQItem[]
}

export interface Vendor {
  id: string
  name: string
  code: string
  contact_email: string
  country: string
  rating: number
  tier: string
  esg_score: number
  iso_certs: string[]
  historical_on_time_rate: number
}

export interface QuotationItem {
  id: string
  quotation_id: string
  item_sku: string
  description: string
  quoted_unit_price: number
  quantity: number
  line_total: number
  lead_time_days: number
  compliance_flag: boolean
}

export interface Quotation {
  id: string
  request_id: string
  vendor_id: string
  vendor_name?: string
  vendor_code?: string
  quote_reference: string
  currency: string
  total_quote_amount: number
  shipping_fee: number
  tax_amount: number
  hidden_fee?: number
  landed_cost?: number
  lead_time_days: number
  warranty_months: number
  payment_terms: string
  compliance_status: string
  compliance_notes: string[]
  uploaded_at: string
  raw_filename?: string
  items: QuotationItem[]
}

// Exact SSE Event shape: {step, status, message, evidence, ts}
export interface RunEvent {
  id?: number
  run_id?: string
  step: string
  status: string
  message: string
  evidence: Record<string, any>
  ts: string
  level?: string
  details?: Record<string, any>
  timestamp?: string
}

export interface EvaluationScore {
  id: string
  run_id: string
  vendor_id: string
  vendor_name: string
  vendor_code: string
  quotation_id: string
  landed_cost: number
  tco: number
  delivery?: {
    quoted_days: number
    variance_days: number
    sla_passed: boolean
    on_time_rate: number
  }
  warranty?: {
    quoted_months: number
    required_months: number
    deficit_months: number
    passed: boolean
  }
  compliance?: {
    passed: boolean
    score: number
    iso_certs: string[]
    esg_score: number
    issues: string[]
    warnings: string[]
  }
  risk?: {
    level: 'LOW' | 'MEDIUM' | 'HIGH'
    score: number
    factors: string[]
  }
  score: number
  price_score: number
  delivery_score: number
  quality_score: number
  compliance_score: number
  composite_score: number
  rank: number
  compliance_passed: boolean
  flag_warnings: string[]
  evidence: string[]
}

export interface EvaluationRun {
  id: string
  request_id: string
  triggered_by: string
  status: string
  weights: {
    price: number
    delivery: number
    quality: number
    compliance: number
  }
  best_vendor_id?: string
  best_vendor_name?: string
  summary_notes?: string
  replan_triggered?: boolean
  replan_reason?: string
  created_at: string
  completed_at?: string
  scores: EvaluationScore[]
}

export interface VendorComparisonDetail {
  vendor: Vendor
  quotation: Quotation
  landed_cost: number
  delivery: {
    quoted_days: number
    variance_days: number
    sla_passed: boolean
    on_time_rate: number
  }
  warranty: {
    quoted_months: number
    required_months: number
    deficit_months: number
    passed: boolean
  }
  compliance: {
    passed: boolean
    score: number
    iso_certs: string[]
    esg_score: number
    issues: string[]
    warnings: string[]
  }
  risk: {
    level: 'LOW' | 'MEDIUM' | 'HIGH'
    score: number
    factors: string[]
  }
  score: number
  evidence: string[]
  tco: number
  tco_breakdown: {
    base_amount: number
    shipping_fee: number
    tax_amount: number
    hidden_fee?: number
    volume_discount: number
    net_direct_cost: number
    landed_cost?: number
    delay_days: number
    lead_time_risk_cost: number
    warranty_deficit_months: number
    warranty_risk_cost: number
    total_risk_cost?: number
    total_tco: number
  }
  compliance_passed: boolean
  compliance_issues: string[]
  lead_time_variance_days: number
  unit_price_savings_pct: number
}

export interface ComparisonMatrix {
  request_id: string
  rfq_title: string
  rfq_budget: number
  vendors_compared: VendorComparisonDetail[]
}

export interface ApprovalAction {
  id: number
  approval_id: string
  stage: string
  role: string
  actor_name: string
  action: string
  notes: string
  action_date: string
}

export interface Approval {
  id: string
  request_id: string
  rfq_title?: string
  recommended_vendor_id: string
  recommended_vendor_name?: string
  current_stage: 'REQUESTER_REVIEW' | 'PROCUREMENT_OFFICER_REVIEW' | 'FINANCE_DIRECTOR_REVIEW' | 'APPROVED' | 'REJECTED'
  status: 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'CHANGES_REQUESTED'
  total_value: number
  comments: string
  evidence_justification?: {
    top_vendor_name: string
    top_vendor_code: string
    landed_cost: number
    authorized_budget: number
    net_savings: number
    savings_percentage: number
    key_evidence: string[]
    competitor_downranking: { vendor: string; reason: string }[]
    replan_handled?: boolean
    replan_notes?: string
  }
  created_at: string
  updated_at: string
  actions: ApprovalAction[]
}

export interface PurchaseOrder {
  po_number: string
  approval_status: string
  current_stage: string
  rfq_id: string
  rfq_title: string
  department: string
  vendor: {
    id: string
    name: string
    code: string
    email: string
    country: string
  }
  terms: {
    currency: string
    payment_terms: string
    lead_time_days: number
    warranty_months: number
  }
  financials: {
    subtotal: number
    shipping_fee: number
    tax_amount: number
    total_po_value: number
  }
  line_items: any[]
  generated_at: string
}

export interface SystemStatus {
  demo_mode: boolean
  app_name: string
  version: string
  gemini_enabled: boolean
  gemini_mode: string
}
