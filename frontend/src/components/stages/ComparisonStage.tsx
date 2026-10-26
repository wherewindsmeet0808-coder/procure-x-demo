import React, { useState, useEffect } from 'react'
import { ShieldCheck, DollarSign, Clock, Award, AlertTriangle, FileText, CheckCircle2 } from 'lucide-react'
import type { ComparisonMatrix, RFQRequest } from '../../types/procurement'
import { fetchComparisonMatrix } from '../../services/api'

interface ComparisonStageProps {
  rfq: RFQRequest | null
  onAdvanceToWhatIf: () => void
}

export const ComparisonStage: React.FC<ComparisonStageProps> = ({ rfq, onAdvanceToWhatIf }) => {
  const [matrix, setMatrix] = useState<ComparisonMatrix | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (rfq) {
      loadMatrix(rfq.id)
    }
  }, [rfq])

  const loadMatrix = async (requestId: string) => {
    try {
      setLoading(true)
      const data = await fetchComparisonMatrix(requestId)
      setMatrix(data)
      setLoading(false)
    } catch (err: any) {
      setLoading(false)
      console.error(err)
    }
  }

  if (!rfq || loading || !matrix) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <p style={{ color: 'var(--text-muted)' }}>Loading Cross-Vendor Comparison Matrix...</p>
      </div>
    )
  }

  const minLandedCost = Math.min(...matrix.vendors_compared.map(v => v.landed_cost))

  return (
    <div>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <span className="tag tag-purple" style={{ marginBottom: '0.4rem' }}>STAGE 4 • CROSS-VENDOR AUDIT</span>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Vendor Comparison Matrix</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Multi-dimensional evaluation across <strong>Landed Cost, Delivery, Warranty, Compliance, Risk, Score, and Evidence</strong>.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={onAdvanceToWhatIf} className="btn btn-primary">
            Tune What-If Ranking →
          </button>
        </div>
      </div>

      {/* Side-by-Side Comparison Cards with 7 Core Dimensions */}
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${matrix.vendors_compared.length}, minmax(300px, 1fr))`, gap: '1.25rem', marginBottom: '2rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
        {matrix.vendors_compared.map((vc) => {
          const isBestPrice = vc.landed_cost === minLandedCost
          const budgetSavings = matrix.rfq_budget - vc.landed_cost
          const isHighRisk = vc.risk.level === 'HIGH'
          const hasHiddenFee = (vc.tco_breakdown.hidden_fee || 0) > 0

          return (
            <div
              key={vc.vendor.id}
              className="card"
              style={{
                margin: 0,
                border: isBestPrice ? '2px solid #2563eb' : isHighRisk ? '2px solid #ea580c' : '1px solid var(--border)',
                background: isBestPrice ? '#f8faff' : isHighRisk ? '#fffaf8' : '#ffffff',
                position: 'relative',
                display: 'flex',
                flexDirection: 'column'
              }}
            >
              {isBestPrice && (
                <div style={{ position: 'absolute', top: '-12px', right: '16px', background: '#2563eb', color: '#ffffff', fontSize: '0.7rem', fontWeight: 700, padding: '0.2rem 0.6rem', borderRadius: '9999px' }}>
                  LOWEST LANDED COST
                </div>
              )}
              {isHighRisk && (
                <div style={{ position: 'absolute', top: '-12px', right: '16px', background: '#ea580c', color: '#ffffff', fontSize: '0.7rem', fontWeight: 700, padding: '0.2rem 0.6rem', borderRadius: '9999px' }}>
                  ELEVATED RISK & CONFLICT
                </div>
              )}

              {/* Header */}
              <div style={{ marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 800 }}>{vc.vendor.name}</h3>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {vc.vendor.code} • {vc.vendor.tier} • {vc.vendor.country}
                </div>
              </div>

              {/* DIMENSION 1: Landed Cost */}
              <div style={{ background: '#f1f5f9', padding: '0.85rem', borderRadius: '8px', marginBottom: '0.75rem' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700 }}>1. CALCULATED LANDED COST</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0f172a' }}>
                  ${vc.landed_cost.toLocaleString()}
                </div>
                <div style={{ fontSize: '0.75rem', color: budgetSavings >= 0 ? '#059669' : '#dc2626', fontWeight: 600, marginTop: '0.2rem' }}>
                  {budgetSavings >= 0 ? `-$${budgetSavings.toLocaleString()} (${vc.unit_price_savings_pct}% under budget)` : `+$${Math.abs(budgetSavings).toLocaleString()} over budget`}
                </div>
                {hasHiddenFee && (
                  <div style={{ fontSize: '0.72rem', color: '#c2410c', fontWeight: 700, marginTop: '0.25rem' }}>
                    Includes +${Number(vc.tco_breakdown.hidden_fee).toLocaleString()} unbundled surcharge
                  </div>
                )}
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.35rem', paddingTop: '0.35rem', borderTop: '1px solid #e2e8f0' }}>
                  Total Evaluated TCO: <strong>${vc.tco.toLocaleString()}</strong>
                </div>
              </div>

              {/* DIMENSION 2: Delivery */}
              <div style={{ padding: '0.5rem 0', borderBottom: '1px solid #e2e8f0', fontSize: '0.8rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-muted)', fontWeight: 700, fontSize: '0.72rem' }}>2. DELIVERY SLA</span>
                  <span className={`tag ${vc.delivery.sla_passed ? 'tag-success' : 'tag-danger'}`} style={{ fontSize: '0.7rem' }}>
                    {vc.delivery.sla_passed ? 'ON TIME' : `+${vc.delivery.variance_days}d SLA BREACH`}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.25rem' }}>
                  <span>Quoted Turnaround:</span>
                  <strong>{vc.delivery.quoted_days} days</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <span>Historical On-Time Rate:</span>
                  <span>{vc.delivery.on_time_rate}%</span>
                </div>
              </div>

              {/* DIMENSION 3: Warranty */}
              <div style={{ padding: '0.5rem 0', borderBottom: '1px solid #e2e8f0', fontSize: '0.8rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-muted)', fontWeight: 700, fontSize: '0.72rem' }}>3. WARRANTY COVERAGE</span>
                  <span className={`tag ${vc.warranty.passed ? 'tag-success' : 'tag-warning'}`} style={{ fontSize: '0.7rem' }}>
                    {vc.warranty.passed ? 'SATISFIED' : 'DEFICIT'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.25rem' }}>
                  <span>Quoted Coverage:</span>
                  <strong>{vc.warranty.quoted_months} months {vc.warranty.deficit_months > 0 && `(-${vc.warranty.deficit_months}mo)`}</strong>
                </div>
              </div>

              {/* DIMENSION 4: Compliance */}
              <div style={{ padding: '0.5rem 0', borderBottom: '1px solid #e2e8f0', fontSize: '0.8rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-muted)', fontWeight: 700, fontSize: '0.72rem' }}>4. COMPLIANCE & STANDARDS</span>
                  <span className={`tag ${vc.compliance.passed ? 'tag-success' : 'tag-danger'}`} style={{ fontSize: '0.7rem' }}>
                    {vc.compliance.passed ? 'PASSED' : 'DEFICIENT'}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap', marginTop: '0.35rem' }}>
                  {vc.compliance.iso_certs.map(c => (
                    <span key={c} className="tag tag-purple" style={{ fontSize: '0.68rem' }}>{c}</span>
                  ))}
                  <span className="tag tag-success" style={{ fontSize: '0.68rem' }}>ESG {vc.compliance.esg_score}</span>
                </div>
              </div>

              {/* DIMENSION 5: Risk */}
              <div style={{ padding: '0.5rem 0', borderBottom: '1px solid #e2e8f0', fontSize: '0.8rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-muted)', fontWeight: 700, fontSize: '0.72rem' }}>5. RISK ASSESSMENT</span>
                  <span className={`tag ${vc.risk.level === 'LOW' ? 'tag-success' : vc.risk.level === 'MEDIUM' ? 'tag-warning' : 'tag-danger'}`} style={{ fontSize: '0.7rem', fontWeight: 800 }}>
                    {vc.risk.level} RISK ({vc.risk.score} pts)
                  </span>
                </div>
              </div>

              {/* DIMENSION 6: Score */}
              <div style={{ padding: '0.5rem 0', borderBottom: '1px solid #e2e8f0', fontSize: '0.8rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-muted)', fontWeight: 700, fontSize: '0.72rem' }}>6. MULTI-ATTRIBUTE SCORE</span>
                  <strong style={{ fontSize: '1.1rem', color: '#2563eb' }}>{vc.score.toFixed(1)} / 100</strong>
                </div>
              </div>

              {/* DIMENSION 7: Evidence */}
              <div style={{ paddingTop: '0.5rem', fontSize: '0.75rem', flex: 1 }}>
                <strong style={{ color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem', fontSize: '0.72rem' }}>
                  7. VERIFIED CONTRACT EVIDENCE:
                </strong>
                <ul style={{ paddingLeft: '1.1rem', color: '#475569', lineHeight: 1.4 }}>
                  {vc.evidence.slice(0, 4).map((ev, i) => (
                    <li key={i} style={{ marginBottom: '0.2rem' }}>{ev}</li>
                  ))}
                </ul>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
