import React, { useState, useEffect } from 'react'
import { Sliders, RefreshCw, Zap, TrendingUp, TrendingDown, Minus, Filter } from 'lucide-react'
import type { EvaluationScore, RFQRequest } from '../../types/procurement'
import { calculateWhatIfRanking } from '../../services/api'

interface WhatIfStageProps {
  rfq: RFQRequest | null
  onAdvanceToApproval: () => void
}

export const WhatIfStage: React.FC<WhatIfStageProps> = ({ rfq, onAdvanceToApproval }) => {
  // Weights
  const [priceWeight, setPriceWeight] = useState(40)
  const [deliveryWeight, setDeliveryWeight] = useState(25)
  const [qualityWeight, setQualityWeight] = useState(20)
  const [complianceWeight, setComplianceWeight] = useState(15)

  // Constraints
  const [budgetFilter, setBudgetFilter] = useState<string>('')
  const [leadTimeFilter, setLeadTimeFilter] = useState<string>('')
  const [warrantyFilter, setWarrantyFilter] = useState<string>('')

  // Scores
  const [scores, setScores] = useState<EvaluationScore[]>([])
  const [baselineScores, setBaselineScores] = useState<Record<string, number>>({})
  const [isRecalculating, setIsRecalculating] = useState(false)

  // Initial calculation
  useEffect(() => {
    if (rfq) {
      runCalculation(40, 25, 20, 15, true)
    }
  }, [rfq])

  // Instant recalculation on slider/filter adjustment without re-extracting quotation documents
  useEffect(() => {
    if (rfq && Object.keys(baselineScores).length > 0) {
      runCalculation(priceWeight, deliveryWeight, qualityWeight, complianceWeight, false)
    }
  }, [priceWeight, deliveryWeight, qualityWeight, complianceWeight, budgetFilter, leadTimeFilter, warrantyFilter])

  const runCalculation = async (
    pw: number,
    dw: number,
    qw: number,
    cw: number,
    isBaseline: boolean
  ) => {
    if (!rfq) return
    try {
      setIsRecalculating(true)
      const res = await calculateWhatIfRanking({
        request_id: rfq.id,
        weights: {
          price: pw / 100,
          delivery: dw / 100,
          quality: qw / 100,
          compliance: cw / 100
        },
        max_budget_limit: budgetFilter ? Number(budgetFilter) : undefined,
        max_lead_time_days: leadTimeFilter ? Number(leadTimeFilter) : undefined,
        min_warranty_months: warrantyFilter ? Number(warrantyFilter) : undefined
      })
      setScores(res)
      if (isBaseline) {
        const bMap: Record<string, number> = {}
        res.forEach(s => {
          bMap[s.vendor_id] = s.rank
        })
        setBaselineScores(bMap)
      }
      setIsRecalculating(false)
    } catch (err: any) {
      setIsRecalculating(false)
      console.error(err)
    }
  }

  // Presets
  const applyPreset = (p: number, d: number, q: number, c: number) => {
    setPriceWeight(p)
    setDeliveryWeight(d)
    setQualityWeight(q)
    setComplianceWeight(c)
  }

  const totalWeights = priceWeight + deliveryWeight + qualityWeight + complianceWeight

  return (
    <div>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <span className="tag tag-purple" style={{ marginBottom: '0.4rem' }}>STAGE 5 • SENSITIVITY MODELING</span>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>What-If Sensitivity Ranking</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Instant in-memory recalculation of vendor rankings across multi-attribute weights (zero re-extraction of quotes).
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={onAdvanceToApproval} className="btn btn-primary">
            Review Recommendation & Approvals →
          </button>
        </div>
      </div>

      {/* Preset Strategy Buttons */}
      <div className="card" style={{ padding: '1rem 1.25rem', marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <Zap size={16} color="#2563eb" />
          <strong style={{ fontSize: '0.85rem' }}>Pre-configured Sourcing Scenarios:</strong>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button
            onClick={() => applyPreset(40, 25, 20, 15)}
            className="btn btn-secondary"
            style={{ fontSize: '0.78rem', padding: '0.35rem 0.75rem' }}
          >
            Balanced Value (40/25/20/15)
          </button>
          <button
            onClick={() => applyPreset(70, 15, 10, 5)}
            className="btn btn-secondary"
            style={{ fontSize: '0.78rem', padding: '0.35rem 0.75rem' }}
          >
            Cost Minimizer (70% Price)
          </button>
          <button
            onClick={() => applyPreset(20, 50, 20, 10)}
            className="btn btn-secondary"
            style={{ fontSize: '0.78rem', padding: '0.35rem 0.75rem' }}
          >
            Urgent SLA (50% Delivery Speed)
          </button>
          <button
            onClick={() => applyPreset(15, 15, 30, 40)}
            className="btn btn-secondary"
            style={{ fontSize: '0.78rem', padding: '0.35rem 0.75rem' }}
          >
            ESG & Risk Averse (40% Compliance)
          </button>
        </div>
      </div>

      {/* Control Sliders & Filters Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.25rem', marginBottom: '1.5rem' }}>
        {/* Sliders Box */}
        <div className="card" style={{ margin: 0, padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Sliders size={16} color="#2563eb" />
              <span>Multi-Attribute Weight Sliders</span>
            </h4>
            <span style={{ fontSize: '0.78rem', color: totalWeights === 100 ? '#059669' : '#f59e0b', fontWeight: 600 }}>
              Sum: {totalWeights}% {totalWeights !== 100 && '(auto-normalized to 100%)'}
            </span>
          </div>

          <div className="slider-group">
            <div className="slider-header">
              <span style={{ color: '#1e293b' }}>Price & Landed Cost Weight</span>
              <strong style={{ color: '#2563eb' }}>{priceWeight}%</strong>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={priceWeight}
              onChange={e => setPriceWeight(Number(e.target.value))}
              className="range-slider"
            />
          </div>

          <div className="slider-group">
            <div className="slider-header">
              <span style={{ color: '#1e293b' }}>Delivery Speed & On-Time SLA</span>
              <strong style={{ color: '#2563eb' }}>{deliveryWeight}%</strong>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={deliveryWeight}
              onChange={e => setDeliveryWeight(Number(e.target.value))}
              className="range-slider"
            />
          </div>

          <div className="slider-group">
            <div className="slider-header">
              <span style={{ color: '#1e293b' }}>Vendor Tier & Historical Quality</span>
              <strong style={{ color: '#2563eb' }}>{qualityWeight}%</strong>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={qualityWeight}
              onChange={e => setQualityWeight(Number(e.target.value))}
              className="range-slider"
            />
          </div>

          <div className="slider-group">
            <div className="slider-header">
              <span style={{ color: '#1e293b' }}>Compliance, ISO & ESG Rating</span>
              <strong style={{ color: '#2563eb' }}>{complianceWeight}%</strong>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={complianceWeight}
              onChange={e => setComplianceWeight(Number(e.target.value))}
              className="range-slider"
            />
          </div>
        </div>

        {/* Constraint Filters Box */}
        <div className="card" style={{ margin: 0, padding: '1.25rem' }}>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '1rem' }}>
            <Filter size={16} color="#8b5cf6" />
            <span>Scenario Constraints</span>
          </h4>

          <div className="form-group" style={{ marginBottom: '0.75rem' }}>
            <label className="form-label" style={{ fontSize: '0.78rem' }}>Max Landed Budget Cap ($)</label>
            <input
              type="number"
              placeholder="e.g. 100000"
              value={budgetFilter}
              onChange={e => setBudgetFilter(e.target.value)}
              className="form-input"
              style={{ fontSize: '0.8rem', padding: '0.45rem' }}
            />
          </div>

          <div className="form-group" style={{ marginBottom: '0.75rem' }}>
            <label className="form-label" style={{ fontSize: '0.78rem' }}>Max Lead Time (Days)</label>
            <input
              type="number"
              placeholder="e.g. 21"
              value={leadTimeFilter}
              onChange={e => setLeadTimeFilter(e.target.value)}
              className="form-input"
              style={{ fontSize: '0.8rem', padding: '0.45rem' }}
            />
          </div>

          <div className="form-group" style={{ marginBottom: '0.75rem' }}>
            <label className="form-label" style={{ fontSize: '0.78rem' }}>Min Warranty (Months)</label>
            <input
              type="number"
              placeholder="e.g. 24"
              value={warrantyFilter}
              onChange={e => setWarrantyFilter(e.target.value)}
              className="form-input"
              style={{ fontSize: '0.8rem', padding: '0.45rem' }}
            />
          </div>

          {(budgetFilter || leadTimeFilter || warrantyFilter) && (
            <button
              onClick={() => {
                setBudgetFilter('')
                setLeadTimeFilter('')
                setWarrantyFilter('')
              }}
              className="btn btn-outline"
              style={{ width: '100%', fontSize: '0.75rem', padding: '0.3rem' }}
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* Recalculated Ranking Table */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <span>Dynamic What-If Ranking Outcome</span>
            {isRecalculating && <RefreshCw size={14} className="spin" color="#2563eb" style={{ marginLeft: '0.5rem' }} />}
          </div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Instantaneous in-memory recalculation (no re-extraction)
          </span>
        </div>

        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Shift</th>
                <th>Vendor</th>
                <th>Calculated Landed Cost</th>
                <th>Total TCO</th>
                <th>Price Score</th>
                <th>Delivery Score</th>
                <th>Quality Score</th>
                <th>Compliance Score</th>
                <th>Composite Score</th>
                <th>Constraint Status</th>
              </tr>
            </thead>
            <tbody>
              {scores.map(sc => {
                const baseRank = baselineScores[sc.vendor_id] || sc.rank
                const rankShift = baseRank - sc.rank
                return (
                  <tr key={sc.vendor_id} style={{ backgroundColor: sc.rank === 1 ? '#f0fdf4' : 'transparent' }}>
                    <td>
                      <strong style={{ fontSize: '1.1rem', color: sc.rank === 1 ? '#059669' : '#1e293b' }}>
                        #{sc.rank}
                      </strong>
                    </td>
                    <td>
                      {rankShift > 0 ? (
                        <span style={{ color: '#059669', display: 'flex', alignItems: 'center', fontSize: '0.8rem', fontWeight: 700 }}>
                          <TrendingUp size={14} /> +{rankShift}
                        </span>
                      ) : rankShift < 0 ? (
                        <span style={{ color: '#dc2626', display: 'flex', alignItems: 'center', fontSize: '0.8rem', fontWeight: 700 }}>
                          <TrendingDown size={14} /> {rankShift}
                        </span>
                      ) : (
                        <span style={{ color: '#94a3b8', display: 'flex', alignItems: 'center', fontSize: '0.8rem' }}>
                          <Minus size={14} /> 0
                        </span>
                      )}
                    </td>
                    <td>
                      <strong>{sc.vendor_name}</strong>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{sc.vendor_code}</div>
                    </td>
                    <td><strong>${sc.landed_cost.toLocaleString()}</strong></td>
                    <td>${sc.tco.toLocaleString()}</td>
                    <td>{sc.price_score.toFixed(1)}</td>
                    <td>{sc.delivery_score.toFixed(1)}</td>
                    <td>{sc.quality_score.toFixed(1)}</td>
                    <td>{sc.compliance_score.toFixed(1)}</td>
                    <td>
                      <strong style={{ color: '#2563eb', fontSize: '1rem' }}>
                        {sc.composite_score.toFixed(1)}
                      </strong>
                    </td>
                    <td>
                      {sc.flag_warnings.some(f => f.includes('what-if')) ? (
                        <span className="tag tag-danger">DISQUALIFIED BY FILTER</span>
                      ) : sc.compliance_passed ? (
                        <span className="tag tag-success">QUALIFIED</span>
                      ) : (
                        <span className="tag tag-warning">ELEVATED RISK</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
