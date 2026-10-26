import React, { useState, useEffect } from 'react'
import { CheckSquare, CheckCircle2, XCircle, AlertCircle, FileText, Printer, Building, UserCheck, ShieldAlert } from 'lucide-react'
import { Approval, PurchaseOrder, RFQRequest } from '../../types/procurement'
import { fetchApproval, submitApprovalAction, fetchPurchaseOrder } from '../../services/api'

interface ApprovalStageProps {
  rfq: RFQRequest | null
  onRefresh: () => void
}

export const ApprovalStage: React.FC<ApprovalStageProps> = ({ rfq, onRefresh }) => {
  const [approval, setApproval] = useState<Approval | null>(null)
  const [po, setPo] = useState<PurchaseOrder | null>(null)
  const [showActionModal, setShowActionModal] = useState(false)
  const [showPoModal, setShowPoModal] = useState(false)
  const [actionType, setActionType] = useState<'APPROVE' | 'REJECT' | 'REQUEST_CHANGES'>('APPROVE')
  const [actorName, setActorName] = useState('Elena Rostova')
  const [role, setRole] = useState('Finance Director')
  const [notes, setNotes] = useState('Verified budget variance and vendor SLA compliance. Approved.')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (rfq) {
      loadApproval(rfq.id)
    }
  }, [rfq])

  const loadApproval = async (requestId: string) => {
    try {
      setLoading(true)
      const data = await fetchApproval(requestId)
      setApproval(data)
      setLoading(false)
    } catch (err: any) {
      setLoading(false)
      console.error(err)
    }
  }

  const handleExecuteAction = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!approval) return

    try {
      const updated = await submitApprovalAction(approval.id, {
        action: actionType,
        actor_name: actorName,
        role: role,
        notes: notes
      })
      setApproval(updated)
      setShowActionModal(false)
      onRefresh()
    } catch (err: any) {
      alert(err.message || 'Action execution failed')
    }
  }

  const handleOpenPO = async () => {
    if (!approval) return
    try {
      const poData = await fetchPurchaseOrder(approval.id)
      setPo(poData)
      setShowPoModal(true)
    } catch (err: any) {
      alert(err.message || 'Failed to generate PO')
    }
  }

  if (!rfq || loading || !approval) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <p style={{ color: 'var(--text-muted)' }}>Loading Approval Workflow...</p>
      </div>
    )
  }

  const stages = [
    { key: 'REQUESTER_REVIEW', label: '1. Sourcing Requester Sign-off', defaultRole: 'Lead Cloud Architect' },
    { key: 'PROCUREMENT_OFFICER_REVIEW', label: '2. Commercial Procurement Officer', defaultRole: 'Strategic Sourcing Manager' },
    { key: 'FINANCE_DIRECTOR_REVIEW', label: '3. Executive Finance Approval', defaultRole: 'Finance Director' }
  ]

  const stageOrder = ['REQUESTER_REVIEW', 'PROCUREMENT_OFFICER_REVIEW', 'FINANCE_DIRECTOR_REVIEW', 'APPROVED']
  const currentStageIdx = stageOrder.indexOf(approval.current_stage)

  return (
    <div>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <span className="tag tag-purple" style={{ marginBottom: '0.4rem' }}>STAGE 6 • GOVERNANCE & SIGNOFF</span>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Recommendation & Multi-Stage Approval</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Formalize supplier award selection with role-based sign-offs, immutable audit logging, and purchase order emission.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          {approval.status !== 'APPROVED' && approval.status !== 'REJECTED' && (
            <button
              onClick={() => {
                const currentStageInfo = stages.find(s => s.key === approval.current_stage)
                if (currentStageInfo) {
                  setRole(currentStageInfo.defaultRole)
                }
                setShowActionModal(true)
              }}
              className="btn btn-primary"
            >
              <UserCheck size={16} />
              Sign-Off Current Stage
            </button>
          )}

          <button onClick={handleOpenPO} className="btn btn-secondary">
            <FileText size={16} />
            Generate Purchase Order (PO)
          </button>
        </div>
      </div>

      {/* Recommended Award Summary Banner */}
      <div className="card" style={{ background: '#f8fafc', borderLeft: '4px solid #2563eb', padding: '1.25rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <span className="tag tag-success" style={{ marginBottom: '0.5rem' }}>OFFICIAL RECOMMENDATION</span>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 800 }}>
              Award Recommendation: {approval.recommended_vendor_name || approval.recommended_vendor_id}
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
              Project: <strong>{approval.rfq_title}</strong> • Total Award Value: <strong>${approval.total_value.toLocaleString()} USD</strong>
            </p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span className={`tag ${approval.status === 'APPROVED' ? 'tag-success' : approval.status === 'REJECTED' ? 'tag-danger' : 'tag-warning'}`} style={{ fontSize: '0.85rem', padding: '0.35rem 0.8rem' }}>
              {approval.status.replace('_', ' ')}
            </span>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
              Workflow Ref: <code>{approval.id}</code>
            </div>
          </div>
        </div>

        <div style={{ marginTop: '1rem', padding: '0.85rem', background: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.85rem' }}>
          <strong>Executive Strategic Rationale:</strong>
          <p style={{ color: '#334155', marginTop: '0.3rem', lineHeight: 1.5 }}>
            {approval.comments || 'Vendor achieved highest multidimensional composite index across Total Cost of Ownership (TCO), ISO compliance guarantees, and delivery turnaround SLAs.'}
          </p>
        </div>
      </div>

      {/* Multi-Step Pipeline Visualizer */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1.25rem' }}>Governance Approval Chain</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
          {stages.map((st, idx) => {
            const isDone = currentStageIdx > idx || approval.status === 'APPROVED'
            const isCurrent = approval.current_stage === st.key && approval.status === 'PENDING_APPROVAL'
            return (
              <div
                key={st.key}
                style={{
                  padding: '1rem',
                  borderRadius: '8px',
                  background: isDone ? '#ecfdf5' : isCurrent ? '#eff6ff' : '#f8fafc',
                  border: `2px solid ${isDone ? '#10b981' : isCurrent ? '#3b82f6' : '#e2e8f0'}`
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: isDone ? '#065f46' : isCurrent ? '#1d4ed8' : '#64748b' }}>
                    {isDone ? 'COMPLETED' : isCurrent ? 'PENDING ACTION' : 'QUEUED'}
                  </span>
                  {isDone ? <CheckCircle2 size={18} color="#10b981" /> : isCurrent ? <AlertCircle size={18} color="#3b82f6" /> : <span style={{ color: '#cbd5e1' }}>○</span>}
                </div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#1e293b' }}>
                  {st.label}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  Authorized Role: <strong>{st.defaultRole}</strong>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Immutable Audit Trail */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <CheckSquare size={18} color="#2563eb" />
            <span>Immutable Sign-off Audit Trail</span>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Tamper-evident SQLite event journal
          </span>
        </div>

        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Workflow Stage</th>
                <th>Signatory</th>
                <th>Role</th>
                <th>Action Taken</th>
                <th>Audit Notes & Justification</th>
              </tr>
            </thead>
            <tbody>
              {approval.actions.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No approval actions logged yet.
                  </td>
                </tr>
              ) : (
                approval.actions.map(act => (
                  <tr key={act.id}>
                    <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      {new Date(act.action_date).toLocaleString()}
                    </td>
                    <td><code>{act.stage}</code></td>
                    <td><strong>{act.actor_name}</strong></td>
                    <td>{act.role}</td>
                    <td>
                      <span className={`tag ${act.action === 'APPROVE' ? 'tag-success' : act.action === 'REJECT' ? 'tag-danger' : 'tag-warning'}`}>
                        {act.action}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8rem' }}>{act.notes}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Sign-off Action Modal */}
      {showActionModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Governance Sign-Off Action</h3>
              <button onClick={() => setShowActionModal(false)} className="btn btn-outline" style={{ padding: '0.2rem 0.5rem' }}>✕</button>
            </div>
            <form onSubmit={handleExecuteAction}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Current Stage</label>
                  <input
                    type="text"
                    disabled
                    value={approval.current_stage}
                    className="form-input"
                    style={{ background: '#f8fafc', color: '#64748b' }}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label className="form-label">Actor Name</label>
                    <input
                      type="text"
                      required
                      value={actorName}
                      onChange={e => setActorName(e.target.value)}
                      className="form-input"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Signatory Role</label>
                    <input
                      type="text"
                      required
                      value={role}
                      onChange={e => setRole(e.target.value)}
                      className="form-input"
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Action</label>
                  <select
                    value={actionType}
                    onChange={e => setActionType(e.target.value as any)}
                    className="form-select"
                  >
                    <option value="APPROVE">APPROVE (Advance to Next Stage)</option>
                    <option value="REQUEST_CHANGES">REQUEST CHANGES (Return to Prior Stage)</option>
                    <option value="REJECT">REJECT (Terminate Workflow)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Sign-Off Justification & Notes</label>
                  <textarea
                    rows={3}
                    required
                    value={notes}
                    onChange={e => setNotes(e.target.value)}
                    className="form-textarea"
                    placeholder="Enter formal justification for this decision..."
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => setShowActionModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button
                  type="submit"
                  className={`btn ${actionType === 'APPROVE' ? 'btn-success' : actionType === 'REJECT' ? 'btn-danger' : 'btn-primary'}`}
                >
                  Record Official Sign-Off
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Purchase Order Modal */}
      {showPoModal && po && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '800px' }}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FileText size={20} color="#2563eb" />
                <h3 style={{ fontSize: '1.15rem', fontWeight: 800 }}>Purchase Order: {po.po_number}</h3>
              </div>
              <button onClick={() => setShowPoModal(false)} className="btn btn-outline" style={{ padding: '0.2rem 0.5rem' }}>✕</button>
            </div>

            <div className="modal-body" style={{ background: '#ffffff', padding: '2rem' }}>
              {/* PO Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '2px solid #e2e8f0', paddingBottom: '1.25rem', marginBottom: '1.5rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#0f172a' }}>ACME ENTERPRISES INC.</h2>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Global Procurement & Sourcing Division</p>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Department: {po.department}</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#2563eb' }}>{po.po_number}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Status: <strong>{po.approval_status}</strong></div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Date: {new Date(po.generated_at).toLocaleDateString()}</div>
                </div>
              </div>

              {/* Vendor & Delivery Box */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem', fontSize: '0.85rem' }}>
                <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px' }}>
                  <strong style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>VENDOR / BENEFICIARY:</strong>
                  <div style={{ fontWeight: 700, fontSize: '1rem', marginTop: '0.25rem' }}>{po.vendor.name}</div>
                  <div>Code: {po.vendor.code} • {po.vendor.country}</div>
                  <div>Email: {po.vendor.email}</div>
                </div>

                <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px' }}>
                  <strong style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>COMMERCIAL TERMS:</strong>
                  <div style={{ marginTop: '0.25rem' }}>Payment Terms: <strong>{po.terms.payment_terms}</strong></div>
                  <div>Delivery SLA: <strong>{po.terms.lead_time_days} Days</strong></div>
                  <div>Warranty Guarantee: <strong>{po.terms.warranty_months} Months</strong></div>
                </div>
              </div>

              {/* Line Items */}
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.5rem' }}>Order Line Items</h4>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', marginBottom: '1.5rem' }}>
                <thead>
                  <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #cbd5e1' }}>
                    <th style={{ padding: '0.5rem', textAlign: 'left' }}>SKU</th>
                    <th style={{ padding: '0.5rem', textAlign: 'left' }}>Description</th>
                    <th style={{ padding: '0.5rem', textAlign: 'center' }}>Qty</th>
                    <th style={{ padding: '0.5rem', textAlign: 'right' }}>Unit Price</th>
                    <th style={{ padding: '0.5rem', textAlign: 'right' }}>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {po.line_items.map((it, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #e2e8f0' }}>
                      <td style={{ padding: '0.5rem' }}><code>{it.item_sku}</code></td>
                      <td style={{ padding: '0.5rem' }}>{it.description}</td>
                      <td style={{ padding: '0.5rem', textAlign: 'center' }}>{it.quantity}</td>
                      <td style={{ padding: '0.5rem', textAlign: 'right' }}>${Number(it.quoted_unit_price).toLocaleString()}</td>
                      <td style={{ padding: '0.5rem', textAlign: 'right', fontWeight: 600 }}>${Number(it.line_total).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Financial Totals */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', fontSize: '0.85rem' }}>
                <div style={{ width: '280px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.25rem 0' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Line Items Direct:</span>
                    <span>${po.financials.subtotal.toLocaleString()}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.25rem 0' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Freight & Handling:</span>
                    <span>+${po.financials.shipping_fee.toLocaleString()}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.25rem 0' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Taxes:</span>
                    <span>+${po.financials.tax_amount.toLocaleString()}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderTop: '2px solid #0f172a', marginTop: '0.5rem', fontSize: '1.05rem', fontWeight: 800 }}>
                    <span>TOTAL AUTHORIZED:</span>
                    <span style={{ color: '#2563eb' }}>${po.financials.total_po_value.toLocaleString()} {po.terms.currency}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button onClick={() => window.print()} className="btn btn-secondary">
                <Printer size={15} />
                Print / Save PDF
              </button>
              <button onClick={() => setShowPoModal(false)} className="btn btn-primary">
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
