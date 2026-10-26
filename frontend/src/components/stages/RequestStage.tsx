import React, { useState } from 'react'
import { Plus, CheckCircle2, Clock, DollarSign, ShieldAlert, Award, FileSpreadsheet } from 'lucide-react'
import { RFQRequest } from '../../types/procurement'
import { createRFQ } from '../../services/api'

interface RequestStageProps {
  rfq: RFQRequest | null
  onRefresh: () => void
  onAdvanceToQuotations: () => void
}

export const RequestStage: React.FC<RequestStageProps> = ({ rfq, onRefresh, onAdvanceToQuotations }) => {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [title, setTitle] = useState('')
  const [department, setDepartment] = useState('Global Engineering & Infrastructure')
  const [category, setCategory] = useState('Hardware & Compute Fleet')
  const [budget, setBudget] = useState(120000)
  const [deadlineDays, setDeadlineDays] = useState(21)
  const [minWarranty, setMinWarranty] = useState(24)
  const [minEsg, setMinEsg] = useState(70)
  const [isoCerts, setIsoCerts] = useState('ISO-9001, ISO-27001')
  
  // Line items for modal
  const [items, setItems] = useState([
    { sku: 'SRV-COMP-X', description: 'Enterprise Dual-Socket Compute Node', quantity: 4, target_unit_price: 18000 }
  ])

  const handleAddItemRow = () => {
    setItems([...items, { sku: '', description: '', quantity: 1, target_unit_price: 1000 }])
  }

  const handleCreateRFQ = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createRFQ({
        title,
        department,
        category,
        budget: Number(budget),
        currency: 'USD',
        deadline_days: Number(deadlineDays),
        min_warranty_months: Number(minWarranty),
        min_esg_score: Number(minEsg),
        required_iso_certs: isoCerts.split(',').map(s => s.trim()).filter(Boolean),
        items: items.map(it => ({
          sku: it.sku,
          description: it.description,
          quantity: Number(it.quantity),
          target_unit_price: Number(it.target_unit_price)
        }))
      })
      setShowCreateModal(false)
      onRefresh()
    } catch (err: any) {
      alert(err.message || 'Error creating RFQ')
    }
  }

  if (!rfq) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <p style={{ color: 'var(--text-muted)' }}>No RFQ Request selected. Reseed demo data or create a new request.</p>
      </div>
    )
  }

  const totalTargetEst = rfq.items.reduce((acc, it) => acc + (it.quantity * it.target_unit_price), 0)

  return (
    <div>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <span className="tag tag-purple" style={{ marginBottom: '0.4rem' }}>STAGE 1 • SOURCING SPECIFICATION</span>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Procurement Request (RFQ)</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Define required bill of materials, budgetary limits, delivery SLAs, and mandatory compliance standards.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={() => setShowCreateModal(true)} className="btn btn-secondary">
            <Plus size={16} />
            New RFQ
          </button>
          <button onClick={onAdvanceToQuotations} className="btn btn-primary">
            Proceed to Quotations
            →
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="card" style={{ margin: 0, padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>AUTHORIZED BUDGET</span>
            <DollarSign size={18} color="#2563eb" />
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: '0.5rem', color: '#1e293b' }}>
            ${rfq.budget.toLocaleString()} <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{rfq.currency}</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#059669', marginTop: '0.25rem', fontWeight: 600 }}>
            Target Sum: ${totalTargetEst.toLocaleString()} ({Math.round((totalTargetEst / rfq.budget) * 100)}% allocation)
          </div>
        </div>

        <div className="card" style={{ margin: 0, padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>MAX LEAD TIME SLA</span>
            <Clock size={18} color="#f59e0b" />
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: '0.5rem', color: '#1e293b' }}>
            {rfq.deadline_days} <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Days</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Strict cutoff for penalty-free dispatch
          </div>
        </div>

        <div className="card" style={{ margin: 0, padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>MANDATORY STANDARDS</span>
            <Award size={18} color="#8b5cf6" />
          </div>
          <div style={{ marginTop: '0.5rem', display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
            {rfq.required_iso_certs.map(c => (
              <span key={c} className="tag tag-success">{c}</span>
            ))}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
            Min ESG: {rfq.min_esg_score} • Min Warranty: {rfq.min_warranty_months} mo
          </div>
        </div>
      </div>

      {/* Main RFQ Specification Card */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <FileSpreadsheet size={18} color="#2563eb" />
            <span>{rfq.title}</span>
            <span className="tag tag-purple" style={{ marginLeft: '0.5rem' }}>{rfq.id}</span>
          </div>
          <span className="tag tag-success">{rfq.status}</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', padding: '0.5rem 0 1.25rem 0', fontSize: '0.85rem' }}>
          <div><strong style={{ color: 'var(--text-muted)' }}>Department:</strong> {rfq.department}</div>
          <div><strong style={{ color: 'var(--text-muted)' }}>Category:</strong> {rfq.category}</div>
          <div><strong style={{ color: 'var(--text-muted)' }}>Created Date:</strong> {new Date(rfq.created_at).toLocaleDateString()}</div>
        </div>

        {/* Bill of Materials / Items Table */}
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, margin: '1rem 0 0.75rem 0' }}>Bill of Materials (Target Line Items)</h3>
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Description</th>
                <th>Qty</th>
                <th>Target Unit Price</th>
                <th>Target Line Total</th>
                <th>Technical Specs</th>
              </tr>
            </thead>
            <tbody>
              {rfq.items.map(it => {
                const lineTot = it.quantity * it.target_unit_price
                return (
                  <tr key={it.id}>
                    <td><code>{it.sku}</code></td>
                    <td style={{ fontWeight: 600 }}>{it.description}</td>
                    <td>{it.quantity}</td>
                    <td>${it.target_unit_price.toLocaleString()}</td>
                    <td><strong>${lineTot.toLocaleString()}</strong></td>
                    <td>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {Object.entries(it.specifications || {}).map(([k, v]) => `${k}: ${v}`).join(' • ') || 'Standard spec'}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Create RFQ */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Create New Procurement RFQ</h3>
              <button onClick={() => setShowCreateModal(false)} className="btn btn-outline" style={{ padding: '0.2rem 0.5rem' }}>✕</button>
            </div>
            <form onSubmit={handleCreateRFQ}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">RFQ Title</label>
                  <input
                    type="text"
                    required
                    value={title}
                    onChange={e => setTitle(e.target.value)}
                    placeholder="e.g. Next-Gen Datacenter Core Switches & Optics"
                    className="form-input"
                  />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label className="form-label">Department</label>
                    <input
                      type="text"
                      value={department}
                      onChange={e => setDepartment(e.target.value)}
                      className="form-input"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Category</label>
                    <input
                      type="text"
                      value={category}
                      onChange={e => setCategory(e.target.value)}
                      className="form-input"
                    />
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label className="form-label">Budget ($)</label>
                    <input
                      type="number"
                      required
                      value={budget}
                      onChange={e => setBudget(Number(e.target.value))}
                      className="form-input"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Deadline (Days)</label>
                    <input
                      type="number"
                      value={deadlineDays}
                      onChange={e => setDeadlineDays(Number(e.target.value))}
                      className="form-input"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Min Warranty (Mo)</label>
                    <input
                      type="number"
                      value={minWarranty}
                      onChange={e => setMinWarranty(Number(e.target.value))}
                      className="form-input"
                    />
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label className="form-label">Min ESG Score (0-100)</label>
                    <input
                      type="number"
                      value={minEsg}
                      onChange={e => setMinEsg(Number(e.target.value))}
                      className="form-input"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Required ISO Certs (comma-separated)</label>
                    <input
                      type="text"
                      value={isoCerts}
                      onChange={e => setIsoCerts(e.target.value)}
                      className="form-input"
                    />
                  </div>
                </div>

                {/* Line Items */}
                <div style={{ marginTop: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <label className="form-label" style={{ margin: 0 }}>Line Items (SKUs)</label>
                    <button type="button" onClick={handleAddItemRow} className="btn btn-outline" style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem' }}>
                      + Add Row
                    </button>
                  </div>
                  {items.map((it, idx) => (
                    <div key={idx} style={{ display: 'grid', gridTemplateColumns: '1fr 2fr 80px 100px', gap: '0.5rem', marginBottom: '0.5rem' }}>
                      <input
                        placeholder="SKU"
                        value={it.sku}
                        onChange={e => {
                          const n = [...items]
                          n[idx].sku = e.target.value
                          setItems(n)
                        }}
                        className="form-input"
                      />
                      <input
                        placeholder="Description"
                        value={it.description}
                        onChange={e => {
                          const n = [...items]
                          n[idx].description = e.target.value
                          setItems(n)
                        }}
                        className="form-input"
                      />
                      <input
                        type="number"
                        placeholder="Qty"
                        value={it.quantity}
                        onChange={e => {
                          const n = [...items]
                          n[idx].quantity = Number(e.target.value)
                          setItems(n)
                        }}
                        className="form-input"
                      />
                      <input
                        type="number"
                        placeholder="Price"
                        value={it.target_unit_price}
                        onChange={e => {
                          const n = [...items]
                          n[idx].target_unit_price = Number(e.target.value)
                          setItems(n)
                        }}
                        className="form-input"
                      />
                    </div>
                  ))}
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setShowCreateModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save & Publish RFQ
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
