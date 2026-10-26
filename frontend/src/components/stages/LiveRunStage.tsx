import React, { useState } from 'react'
import { PlayCircle, CheckCircle2, Clock, Terminal, Trophy, AlertTriangle, RefreshCw, AlertCircle, ShieldAlert } from 'lucide-react'
import type { RFQRequest, EvaluationRun, RunEvent } from '../../types/procurement'
import { triggerEvaluationRun } from '../../services/api'

interface LiveRunStageProps {
  rfq: RFQRequest | null
  onAdvanceToComparison: () => void
}

export const LiveRunStage: React.FC<LiveRunStageProps> = ({ rfq, onAdvanceToComparison }) => {
  const [isRunning, setIsRunning] = useState(false)
  const [latestRun, setLatestRun] = useState<EvaluationRun | null>(null)
  const [events, setEvents] = useState<RunEvent[]>([])
  const [replanEvent, setReplanEvent] = useState<RunEvent | null>(null)
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0)
  
  // Custom weights
  const [priceWeight, setPriceWeight] = useState(40)
  const [deliveryWeight, setDeliveryWeight] = useState(25)
  const [qualityWeight, setQualityWeight] = useState(20)
  const [complianceWeight, setComplianceWeight] = useState(15)

  const stepsList = [
    { key: 'INTAKE', label: '1. Bid Intake' },
    { key: 'PARSING', label: '2. Normalization' },
    { key: 'COMPLIANCE_AUDIT', label: '3. Compliance Audit' },
    { key: 'CONFLICT_DETECTION', label: '4. Conflict Audit' },
    { key: 'REPLAN', label: '5. Agent Re-Plan' },
    { key: 'TCO_MODELING', label: '6. Landed Cost & TCO' },
    { key: 'WHAT_IF_RANKING', label: '7. Multi-Attribute Rank' },
    { key: 'RECOMMENDATION', label: '8. Recommendation' }
  ]

  const handleStartRun = async () => {
    if (!rfq) return
    setIsRunning(true)
    setEvents([])
    setReplanEvent(null)
    setCurrentStepIndex(0)

    try {
      const run = await triggerEvaluationRun({
        request_id: rfq.id,
        triggered_by: 'PROCURE-X Autonomous Sourcing Engine',
        weights: {
          price: priceWeight / 100,
          delivery: deliveryWeight / 100,
          quality: qualityWeight / 100,
          compliance: complianceWeight / 100
        }
      })
      setLatestRun(run)

      // Connect to Server-Sent Events (SSE) live event stream
      // Event shape: {step, status, message, evidence, ts}
      const eventSource = new EventSource(`/api/runs/${run.id}/stream`)
      
      eventSource.onmessage = (e) => {
        try {
          const evData: RunEvent = JSON.parse(e.data)
          setEvents(prev => [...prev, evData])
          
          // Check for visible REPLAN event
          if (evData.status === 'REPLAN' || evData.step === 'REPLAN') {
            setReplanEvent(evData)
          }

          // Advance step index
          const foundIdx = stepsList.findIndex(s => s.key === evData.step)
          if (foundIdx !== -1) {
            setCurrentStepIndex(foundIdx)
          }
        } catch (err) {
          console.error('SSE parse error:', err)
        }
      }

      eventSource.addEventListener('done', () => {
        eventSource.close()
        setIsRunning(false)
        setCurrentStepIndex(stepsList.length)
      })

      eventSource.onerror = () => {
        eventSource.close()
        setIsRunning(false)
      }
    } catch (err: any) {
      setIsRunning(false)
      alert(err.message || 'Run execution failed')
    }
  }

  return (
    <div>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <span className="tag tag-purple" style={{ marginBottom: '0.4rem' }}>STAGE 3 • AUTONOMOUS EVALUATION ENGINE</span>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Live Agent Run (SSE Event Stream)</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Real-time streaming agent evaluation emitting structured events: <code>{'{step, status, message, evidence, ts}'}</code>.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={handleStartRun}
            disabled={isRunning}
            className="btn btn-primary"
            style={{ minWidth: '180px', justifyContent: 'center' }}
          >
            {isRunning ? (
              <>
                <RefreshCw size={16} className="spin" />
                Agent Evaluating...
              </>
            ) : (
              <>
                <PlayCircle size={16} />
                Execute Agent Run
              </>
            )}
          </button>
          <button onClick={onAdvanceToComparison} className="btn btn-success">
            View Comparison Matrix →
          </button>
        </div>
      </div>

      {/* Weights Config Box */}
      <div className="card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 700 }}>Run Evaluation Weight Distribution</h4>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Total: <strong>{priceWeight + deliveryWeight + qualityWeight + complianceWeight}%</strong>
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
          <div>
            <label className="form-label">Price Weight ({priceWeight}%)</label>
            <input
              type="range"
              min="0"
              max="100"
              value={priceWeight}
              disabled={isRunning}
              onChange={e => setPriceWeight(Number(e.target.value))}
              className="range-slider"
            />
          </div>
          <div>
            <label className="form-label">Delivery Speed ({deliveryWeight}%)</label>
            <input
              type="range"
              min="0"
              max="100"
              value={deliveryWeight}
              disabled={isRunning}
              onChange={e => setDeliveryWeight(Number(e.target.value))}
              className="range-slider"
            />
          </div>
          <div>
            <label className="form-label">Vendor Quality ({qualityWeight}%)</label>
            <input
              type="range"
              min="0"
              max="100"
              value={qualityWeight}
              disabled={isRunning}
              onChange={e => setQualityWeight(Number(e.target.value))}
              className="range-slider"
            />
          </div>
          <div>
            <label className="form-label">Compliance & ESG ({complianceWeight}%)</label>
            <input
              type="range"
              min="0"
              max="100"
              value={complianceWeight}
              disabled={isRunning}
              onChange={e => setComplianceWeight(Number(e.target.value))}
              className="range-slider"
            />
          </div>
        </div>
      </div>

      {/* Visible REPLAN Event Alert Card */}
      {replanEvent && (
        <div
          className="card"
          style={{
            background: '#fff7ed',
            border: '2px solid #ea580c',
            borderLeft: '8px solid #c2410c',
            padding: '1.25rem',
            marginBottom: '1.5rem',
            boxShadow: '0 4px 14px rgba(234, 88, 12, 0.15)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="tag tag-danger" style={{ fontWeight: 800, letterSpacing: '0.05em' }}>
                ⚠️ AGENT REPLAN TRIGGERED
              </span>
              <span style={{ fontSize: '0.8rem', color: '#9a3412', fontWeight: 600 }}>
                Quotation Conflict & Hidden Surcharge Identified
              </span>
            </div>
            <span style={{ fontSize: '0.75rem', color: '#9a3412', fontFamily: 'monospace' }}>
              ts: {new Date(replanEvent.ts).toLocaleTimeString()}
            </span>
          </div>

          <p style={{ fontSize: '0.9rem', color: '#7c2d12', fontWeight: 600, lineHeight: 1.4, marginBottom: '0.75rem' }}>
            {replanEvent.message}
          </p>

          <div style={{ background: '#ffffff', border: '1px solid #fdba74', borderRadius: '6px', padding: '0.75rem', fontSize: '0.8rem' }}>
            <strong style={{ color: '#9a3412', display: 'block', marginBottom: '0.3rem' }}>VERIFIED EVIDENCE EXTRACT:</strong>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.5rem' }}>
              <div>Trigger Clause: <strong>{replanEvent.evidence.clause || replanEvent.evidence.trigger}</strong></div>
              <div>Hidden Fee Amount: <strong style={{ color: '#dc2626' }}>${Number(replanEvent.evidence.hidden_fee || 3500).toLocaleString()}</strong></div>
              <div>Delivery SLA Breach: <strong style={{ color: '#dc2626' }}>+{replanEvent.evidence.sla_breach_days || 5} Days</strong></div>
              <div>Agent Action: <strong style={{ color: '#059669' }}>{replanEvent.evidence.replan_action || 'Recalibrated Landed Cost and risk penalties'}</strong></div>
            </div>
          </div>
        </div>
      )}

      {/* Live Pipeline Stepper */}
      <div className="card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem' }}>Automated Agent Stepper</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(135px, 1fr))', gap: '0.5rem' }}>
          {stepsList.map((step, idx) => {
            const isCompleted = currentStepIndex > idx || (!isRunning && events.length > 0)
            const isCurrent = currentStepIndex === idx && isRunning
            const isReplanStep = step.key === 'REPLAN'
            return (
              <div
                key={step.key}
                style={{
                  padding: '0.65rem 0.5rem',
                  borderRadius: '8px',
                  background: isReplanStep && isCompleted ? '#ffedd5' : isCompleted ? '#ecfdf5' : isCurrent ? '#eff6ff' : '#f8fafc',
                  border: `1px solid ${isReplanStep && isCompleted ? '#ea580c' : isCompleted ? '#a7f3d0' : isCurrent ? '#93c5fd' : '#e2e8f0'}`,
                  transition: 'all 0.3s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', fontWeight: 700, color: isReplanStep && isCompleted ? '#c2410c' : isCompleted ? '#065f46' : isCurrent ? '#1d4ed8' : '#64748b' }}>
                  {isCompleted ? <CheckCircle2 size={14} /> : isCurrent ? <Clock size={14} className="spin" /> : <span>○</span>}
                  <span>{step.label}</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Terminal Live Stream Feed */}
      <div className="card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
        <div className="card-header" style={{ paddingBottom: '0.5rem', marginBottom: '0.75rem' }}>
          <div className="card-title">
            <Terminal size={18} color="#38bdf8" />
            <span>SSE Stream: <code>{'{step, status, message, evidence, ts}'}</code></span>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {events.length} events received
          </span>
        </div>

        <div className="terminal-window">
          {events.length === 0 ? (
            <div style={{ color: '#64748b', textAlign: 'center', padding: '2rem' }}>
              Click <strong>"Execute Agent Run"</strong> above to launch live SSE stream...
            </div>
          ) : (
            events.map((ev, i) => {
              const isReplan = ev.status === 'REPLAN' || ev.step === 'REPLAN'
              const isWarn = ev.status === 'WARNING' || ev.step === 'CONFLICT_DETECTION'
              return (
                <div key={i} className="terminal-line" style={{ color: isReplan ? '#fb923c' : isWarn ? '#fde047' : '#e2e8f0' }}>
                  <span className="term-time">[{new Date(ev.ts).toLocaleTimeString()}]</span>
                  <span className="term-step">[{ev.step}]</span>
                  <span style={{ color: isReplan ? '#f97316' : '#38bdf8', fontWeight: 700 }}>[{ev.status}]</span>
                  <span className="term-msg">{ev.message}</span>
                  {Object.keys(ev.evidence || {}).length > 0 && (
                    <span style={{ color: '#94a3b8', fontSize: '0.72rem', marginLeft: 'auto' }}>
                      evidence={JSON.stringify(ev.evidence)}
                    </span>
                  )}
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* Final Run Scores Card */}
      {latestRun && latestRun.scores.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Trophy size={18} color="#f59e0b" />
              <span>Calibrated Ranking Scorecard</span>
              <span className="tag tag-success" style={{ marginLeft: '0.5rem' }}>COMPLETED</span>
              {latestRun.replan_triggered && (
                <span className="tag tag-danger" style={{ marginLeft: '0.5rem' }}>REPLAN APPLIED</span>
              )}
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Top Match: <strong>{latestRun.best_vendor_name}</strong>
            </span>
          </div>

          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Vendor</th>
                  <th>Landed Cost ($)</th>
                  <th>Total TCO ($)</th>
                  <th>Price Score</th>
                  <th>Delivery Score</th>
                  <th>Quality Score</th>
                  <th>Compliance Score</th>
                  <th>Composite Score</th>
                  <th>Risk Tier</th>
                </tr>
              </thead>
              <tbody>
                {latestRun.scores.map(sc => (
                  <tr key={sc.id} style={{ backgroundColor: sc.rank === 1 ? '#f0fdf4' : 'transparent' }}>
                    <td>
                      <strong style={{ fontSize: '1rem', color: sc.rank === 1 ? '#059669' : '#334155' }}>
                        #{sc.rank}
                      </strong>
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
                      <strong style={{ color: '#2563eb', fontSize: '0.95rem' }}>
                        {sc.composite_score.toFixed(1)}
                      </strong>
                    </td>
                    <td>
                      <span className={`tag ${sc.compliance_passed ? 'tag-success' : 'tag-warning'}`}>
                        {sc.compliance_passed ? 'LOW RISK' : 'HIGH RISK'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
