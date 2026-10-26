import React, { useState } from 'react'
import { UploadCloud, CheckCircle2, AlertTriangle, Download, ChevronDown, ChevronUp, Building, Zap, Plus } from 'lucide-react'
import type { Quotation, Vendor, RFQRequest } from '../../types/procurement'
import { uploadQuotationFile, loadSampleQuotation } from '../../services/api'

interface QuotationStageProps {
  rfq: RFQRequest | null
  quotations: Quotation[]
  vendors: Vendor[]
  onRefresh: () => void
  onAdvanceToLiveRun: () => void
}

export const QuotationStage: React.FC<QuotationStageProps> = ({
  rfq,
  quotations,
  vendors,
  onRefresh,
  onAdvanceToLiveRun
}) => {
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [selectedVendorId, setSelectedVendorId] = useState(vendors[0]?.id || 'VEND-001')
  const [quoteRef, setQuoteRef] = useState(`QUOTE-${Date.now().toString().slice(-4)}`)
  const [leadTime, setLeadTime] = useState(14)
  const [warranty, setWarranty] = useState(24)
  const [shippingFee, setShippingFee] = useState(1500)
  const [taxAmount, setTaxAmount] = useState(4500)
  const [hiddenFee, setHiddenFee] = useState(0)
  const [paymentTerms, setPaymentTerms] = useState('Net 30')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isLoadingSample, setIsLoadingSample] = useState(false)
  const [expandedQuoteId, setExpandedQuoteId] = useState<string | null>(null)

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!rfq) return
    if (!selectedFile) {
      alert('Please select a CSV or JSON quotation file')
      return
    }

    const formData = new FormData()
    formData.append('request_id', rfq.id)
    formData.append('vendor_id', selectedVendorId)
    formData.append('quote_reference', quoteRef)
    formData.append('lead_time_days', leadTime.toString())
    formData.append('warranty_months', warranty.toString())
    formData.append('shipping_fee', shippingFee.toString())
    formData.append('tax_amount', taxAmount.toString())
    formData.append('hidden_fee', hiddenFee.toString())
    formData.append('payment_terms', paymentTerms)
    formData.append('file', selectedFile)

    try {
      setIsUploading(true)
      await uploadQuotationFile(formData)
      setIsUploading(false)
      setShowUploadModal(false)
      setSelectedFile(null)
      onRefresh()
    } catch (err: any) {
      setIsUploading(false)
      alert(err.message || 'Upload failed')
    }
  }

  const handleQuickLoad = async () => {
    if (!rfq) return
    try {
      setIsLoadingSample(true)
      await loadSampleQuotation(rfq.id, selectedVendorId)
      setIsLoadingSample(false)
      onRefresh()
    } catch (err: any) {
      setIsLoadingSample(false)
      alert(err.message || 'Quick load failed')
    }
  }

  const handleDownloadSampleCSV = () => {
    const csvData = `sku,description,unit_price,quantity,lead_time
SRV-AI-800,8x GPU High-Density Server,15200.00,4,14
SW-NET-400G,400GbE Spine-Leaf Switch,7800.00,2,14
UPS-MOD-10K,10kVA Modular UPS,2950.00,4,10
CAB-FBR-OM4,OM4 Low-Latency Fiber Cable,390.00,20,7
`
    const blob = new Blob([csvData], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'sample_vendor_quotation.csv'
    a.click()
  }

  return (
    <div>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <span className="tag tag-purple" style={{ marginBottom: '0.4rem' }}>STAGE 2 • SUPPLIER BID INTAKE</span>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Quotation Upload & Intake</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Ingest and normalize vendor commercial proposals with automatic line-item parsing (zero OCR required).
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.65rem' }}>
          <button
            onClick={handleQuickLoad}
            disabled={isLoadingSample}
            className="btn btn-secondary"
            title="1-click load a realistic commercial quotation"
          >
            <Zap size={15} color="#2563eb" />
            {isLoadingSample ? 'Loading...' : '⚡ Quick Load Quote'}
          </button>
          <button onClick={handleDownloadSampleCSV} className="btn btn-outline" style={{ fontSize: '0.8rem' }}>
            <Download size={14} />
            Sample CSV
          </button>
          <button onClick={() => setShowUploadModal(true)} className="btn btn-primary">
            <UploadCloud size={16} />
            Upload File
          </button>
          <button onClick={onAdvanceToLiveRun} className="btn btn-success">
            Launch Evaluation Run →
          </button>
        </div>
      </div>

      {/* Quotations Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem', marginBottom: '1.5rem' }}>
        {quotations.map(q => {
          const isExpanded = expandedQuoteId === q.id
          const hasHiddenFee = (q.hidden_fee || 0) > 0
          const isWarning = q.compliance_status === 'WARNING' || q.compliance_notes.length > 0 || hasHiddenFee
          return (
            <div key={q.id} className="card" style={{ margin: 0, padding: '1.25rem', borderLeft: `4px solid ${isWarning ? '#f59e0b' : '#10b981'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 700, fontSize: '1.05rem' }}>
                    <Building size={16} color="#475569" />
                    <span>{q.vendor_name || q.vendor_id}</span>
                  </div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Ref: <code>{q.quote_reference}</code>
                  </span>
                </div>
                <span className={`tag ${isWarning ? 'tag-warning' : 'tag-success'}`} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  {isWarning ? <AlertTriangle size={12} /> : <CheckCircle2 size={12} />}
                  {isWarning ? 'AUDIT ALERT' : 'VERIFIED'}
                </span>
              </div>

              {/* Financial & Terms Summary */}
              <div style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: '8px', marginBottom: '0.75rem', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Base Quote Amount:</span>
                  <strong>${q.total_quote_amount.toLocaleString()} {q.currency}</strong>
                </div>
                {hasHiddenFee && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', color: '#dc2626', fontWeight: 600, fontSize: '0.78rem' }}>
                    <span>Fine Print Surcharge:</span>
                    <span>+${Number(q.hidden_fee).toLocaleString()}</span>
                  </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  <span>Freight & Tax:</span>
                  <span>+${(q.shipping_fee + q.tax_amount).toLocaleString()}</span>
                </div>
                {q.landed_cost && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.4rem', paddingTop: '0.4rem', borderTop: '1px solid #e2e8f0', fontWeight: 700 }}>
                    <span style={{ color: '#0f172a' }}>Calculated Landed Cost:</span>
                    <span style={{ color: '#2563eb' }}>${q.landed_cost.toLocaleString()}</span>
                  </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.4rem', paddingTop: '0.4rem', borderTop: '1px solid #e2e8f0', fontSize: '0.78rem' }}>
                  <span>Lead Time: <strong>{q.lead_time_days} days</strong></span>
                  <span>Warranty: <strong>{q.warranty_months} mo</strong></span>
                  <span>Terms: <strong>{q.payment_terms}</strong></span>
                </div>
              </div>

              {/* Compliance / Hidden Fee Notes if any */}
              {isWarning && (
                <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '6px', padding: '0.5rem', marginBottom: '0.75rem', fontSize: '0.75rem', color: '#92400e' }}>
                  <strong>Contract Audit Flags:</strong>
                  <ul style={{ paddingLeft: '1.2rem', marginTop: '0.2rem' }}>
                    {hasHiddenFee && <li>Section 4.2: Unbundled ${Number(q.hidden_fee).toLocaleString()} logistics surcharge detected</li>}
                    {q.compliance_notes.map((note, idx) => (
                      <li key={idx}>{note}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Accordion Toggle for Line Items */}
              <button
                onClick={() => setExpandedQuoteId(isExpanded ? null : q.id)}
                className="btn btn-outline"
                style={{ width: '100%', justifyContent: 'space-between', fontSize: '0.78rem', padding: '0.4rem 0.65rem' }}
              >
                <span>{q.items.length} Normalized Line Items</span>
                {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>

              {/* Expanded Line Items */}
              {isExpanded && (
                <div style={{ marginTop: '0.75rem', borderTop: '1px solid #e2e8f0', paddingTop: '0.5rem' }}>
                  <table style={{ width: '100%', fontSize: '0.75rem', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ color: 'var(--text-muted)', textAlign: 'left' }}>
                        <th style={{ padding: '0.3rem 0' }}>SKU</th>
                        <th style={{ padding: '0.3rem 0' }}>Unit</th>
                        <th style={{ padding: '0.3rem 0' }}>Qty</th>
                        <th style={{ padding: '0.3rem 0', textAlign: 'right' }}>Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {q.items.map(it => (
                        <tr key={it.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                          <td style={{ padding: '0.35rem 0' }}><code>{it.item_sku}</code></td>
                          <td style={{ padding: '0.35rem 0' }}>${it.quoted_unit_price.toLocaleString()}</td>
                          <td style={{ padding: '0.35rem 0' }}>{it.quantity}</td>
                          <td style={{ padding: '0.35rem 0', textAlign: 'right', fontWeight: 600 }}>
                            ${it.line_total.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Upload Commercial Quotation</h3>
              <button onClick={() => setShowUploadModal(false)} className="btn btn-outline" style={{ padding: '0.2rem 0.5rem' }}>✕</button>
            </div>
            <form onSubmit={handleUploadSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Vendor Directory Match</label>
                  <select
                    value={selectedVendorId}
                    onChange={e => setSelectedVendorId(e.target.value)}
                    className="form-select"
                  >
                    {vendors.map(v => (
                      <option key={v.id} value={v.id}>
                        {v.name} ({v.code} • {v.tier} • Rating {v.rating}★)
                      </option>
                    ))}
                  </select>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label className="form-label">Quote Reference ID</label>
                    <input
                      type="text"
                      required
                      value={quoteRef}
                      onChange={e => setQuoteRef(e.target.value)}
                      className="form-input"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Quoted Lead Time (Days)</label>
                    <input
                      type="number"
                      required
                      value={leadTime}
                      onChange={e => setLeadTime(Number(e.target.value))}
                      className="form-input"
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '0.75rem' }}>
                  <div className="form-group">
                    <label className="form-label">Warranty (Mo)</label>
                    <input
                      type="number"
                      required
                      value={warranty}
                      onChange={e => setWarranty(Number(e.target.value))}
                      className="form-input"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Freight ($)</label>
                    <input
                      type="number"
                      value={shippingFee}
                      onChange={e => setShippingFee(Number(e.target.value))}
                      className="form-input"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Tax ($)</label>
                    <input
                      type="number"
                      value={taxAmount}
                      onChange={e => setTaxAmount(Number(e.target.value))}
                      className="form-input"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Hidden Surcharge ($)</label>
                    <input
                      type="number"
                      value={hiddenFee}
                      onChange={e => setHiddenFee(Number(e.target.value))}
                      className="form-input"
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Payment Terms</label>
                  <select
                    value={paymentTerms}
                    onChange={e => setPaymentTerms(e.target.value)}
                    className="form-select"
                  >
                    <option value="Net 30">Net 30 (Standard Enterprise)</option>
                    <option value="Net 45">Net 45</option>
                    <option value="Net 60">Net 60</option>
                    <option value="Immediate Due">Immediate Due (Requires Exception)</option>
                  </select>
                </div>

                {/* File Dropzone */}
                <div className="form-group">
                  <label className="form-label">Quotation File (CSV or JSON)</label>
                  <div style={{ border: '2px dashed #cbd5e1', borderRadius: '8px', padding: '1.5rem', textAlign: 'center', background: '#f8fafc' }}>
                    <UploadCloud size={32} color="#64748b" style={{ margin: '0 auto 0.5rem auto' }} />
                    <p style={{ fontSize: '0.85rem', color: '#475569', marginBottom: '0.5rem' }}>
                      {selectedFile ? selectedFile.name : 'Select or drop quotation document'}
                    </p>
                    <input
                      type="file"
                      accept=".csv,.json"
                      onChange={e => {
                        if (e.target.files && e.target.files[0]) {
                          setSelectedFile(e.target.files[0])
                        }
                      }}
                      style={{ fontSize: '0.8rem' }}
                    />
                  </div>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => setShowUploadModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={isUploading} className="btn btn-primary">
                  {isUploading ? 'Parsing File...' : 'Normalize & Ingest Quotation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
