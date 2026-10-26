import React from 'react'
import { ShieldCheck, RefreshCw, Cpu, Database } from 'lucide-react'
import type { SystemStatus, RFQRequest } from '../types/procurement'

interface HeaderProps {
  status: SystemStatus | null
  rfqs: RFQRequest[]
  selectedRfqId: string
  onSelectRfq: (id: string) => void
  onResetDemo: () => void
  isResetting: boolean
}

export const Header: React.FC<HeaderProps> = ({
  status,
  rfqs,
  selectedRfqId,
  onSelectRfq,
  onResetDemo,
  isResetting
}) => {
  return (
    <header className="top-header">
      <div className="brand-section">
        <div className="brand-logo">
          <ShieldCheck size={24} color="#ffffff" />
        </div>
        <div>
          <h1 className="brand-title">PROCURE-X</h1>
          <p className="brand-subtitle">Autonomous Deterministic Procurement & What-If Sourcing System</p>
        </div>
      </div>

      <div className="header-actions">
        {/* RFQ Selector */}
        {rfqs.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Active RFQ:</span>
            <select
              value={selectedRfqId}
              onChange={(e) => onSelectRfq(e.target.value)}
              className="form-select"
              style={{ padding: '0.35rem 0.65rem', fontSize: '0.8rem', width: 'auto', backgroundColor: '#1e293b', color: '#f8fafc', borderColor: '#334155' }}
            >
              {rfqs.map(r => (
                <option key={r.id} value={r.id}>
                  {r.id} — {r.title.slice(0, 32)}...
                </option>
              ))}
            </select>
          </div>
        )}

        {/* DEMO_MODE Badge */}
        <span className="badge-pill badge-demo">
          <Database size={13} />
          DEMO MODE
        </span>

        {/* Gemini AI Status Badge */}
        <span className={`badge-pill ${status?.gemini_enabled ? 'badge-ai-online' : 'badge-ai-offline'}`}>
          <Cpu size={13} />
          {status?.gemini_enabled ? 'Gemini 1.5 Online' : 'Offline Deterministic Heuristic'}
        </span>

        {/* Reset / Reseed Demo Data */}
        <button
          onClick={onResetDemo}
          disabled={isResetting}
          className="btn btn-outline"
          style={{ borderColor: '#334155', color: '#cbd5e1', fontSize: '0.78rem', padding: '0.35rem 0.75rem' }}
          title="Reset database to realistic procurement seed baseline"
        >
          <RefreshCw size={13} className={isResetting ? 'spin' : ''} />
          {isResetting ? 'Reseeding...' : 'Reset Demo'}
        </button>
      </div>
    </header>
  )
}
