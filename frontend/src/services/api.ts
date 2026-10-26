import type {
  RFQRequest, Vendor, Quotation, EvaluationRun, RunEvent,
  ComparisonMatrix, EvaluationScore, Approval, PurchaseOrder, SystemStatus
} from '../types/procurement'

const API_BASE = '/api'

export async function fetchSystemStatus(): Promise<SystemStatus> {
  const res = await fetch(`${API_BASE}/demo/status`)
  if (!res.ok) throw new Error('Failed to fetch system status')
  return res.json()
}

export async function resetDemoData(): Promise<any> {
  const res = await fetch(`${API_BASE}/demo/reset`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to reset demo data')
  return res.json()
}

export async function fetchRFQs(): Promise<RFQRequest[]> {
  const res = await fetch(`${API_BASE}/requests`)
  if (!res.ok) throw new Error('Failed to fetch RFQs')
  return res.json()
}

export async function fetchRFQ(id: string): Promise<RFQRequest> {
  const res = await fetch(`${API_BASE}/requests/${id}`)
  if (!res.ok) throw new Error(`Failed to fetch RFQ ${id}`)
  return res.json()
}

export async function createRFQ(payload: any): Promise<RFQRequest> {
  const res = await fetch(`${API_BASE}/requests`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!res.ok) throw new Error('Failed to create RFQ')
  return res.json()
}

export async function fetchVendors(): Promise<Vendor[]> {
  const res = await fetch(`${API_BASE}/vendors`)
  if (!res.ok) throw new Error('Failed to fetch vendors')
  return res.json()
}

export async function fetchQuotations(requestId?: string): Promise<Quotation[]> {
  const url = requestId ? `${API_BASE}/quotations?request_id=${requestId}` : `${API_BASE}/quotations`
  const res = await fetch(url)
  if (!res.ok) throw new Error('Failed to fetch quotations')
  return res.json()
}

export async function uploadQuotationFile(formData: FormData): Promise<Quotation> {
  const res = await fetch(`${API_BASE}/quotations/upload`, {
    method: 'POST',
    body: formData
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload error' }))
    throw new Error(err.detail || 'Failed to upload quotation file')
  }
  return res.json()
}

export async function loadSampleQuotation(requestId: string, vendorId: string): Promise<Quotation> {
  const res = await fetch(`${API_BASE}/quotations/load-sample?request_id=${requestId}&vendor_id=${vendorId}`, {
    method: 'POST'
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to load sample quote' }))
    throw new Error(err.detail || 'Failed to load sample quotation')
  }
  return res.json()
}

export async function triggerEvaluationRun(payload: {
  request_id: string
  triggered_by?: string
  weights?: { price: number; delivery: number; quality: number; compliance: number }
}): Promise<EvaluationRun> {
  const res = await fetch(`${API_BASE}/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!res.ok) throw new Error('Failed to trigger evaluation run')
  return res.json()
}

export async function fetchRunEvents(runId: string): Promise<RunEvent[]> {
  const res = await fetch(`${API_BASE}/runs/${runId}/events`)
  if (!res.ok) throw new Error('Failed to fetch run events')
  return res.json()
}

export async function fetchComparisonMatrix(requestId: string): Promise<ComparisonMatrix> {
  const res = await fetch(`${API_BASE}/comparison/${requestId}`)
  if (!res.ok) throw new Error('Failed to fetch comparison matrix')
  return res.json()
}

export async function calculateWhatIfRanking(payload: {
  request_id: string
  weights: { price: number; delivery: number; quality: number; compliance: number }
  max_budget_limit?: number
  max_lead_time_days?: number
  min_warranty_months?: number
}): Promise<EvaluationScore[]> {
  const res = await fetch(`${API_BASE}/ranking/what-if`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!res.ok) throw new Error('Failed to calculate what-if ranking')
  return res.json()
}

export async function fetchApproval(requestId: string): Promise<Approval> {
  const res = await fetch(`${API_BASE}/approvals/${requestId}`)
  if (!res.ok) throw new Error('Failed to fetch approval workflow')
  return res.json()
}

export async function submitApprovalAction(approvalId: string, payload: {
  action: string
  actor_name: string
  role: string
  notes?: string
}): Promise<Approval> {
  const res = await fetch(`${API_BASE}/approvals/${approvalId}/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Action failed' }))
    throw new Error(err.detail || 'Failed to submit approval action')
  }
  return res.json()
}

export async function fetchPurchaseOrder(approvalId: string): Promise<PurchaseOrder> {
  const res = await fetch(`${API_BASE}/approvals/${approvalId}/po`)
  if (!res.ok) throw new Error('Failed to fetch Purchase Order')
  return res.json()
}
