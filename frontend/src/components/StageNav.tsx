import React from 'react'
import { FileText, UploadCloud, PlayCircle, BarChart3, Sliders, CheckSquare } from 'lucide-react'

export type StageId = 'request' | 'quotations' | 'live-run' | 'comparison' | 'what-if' | 'approval'

interface StageNavProps {
  currentStage: StageId
  onSelectStage: (stage: StageId) => void
}

export const StageNav: React.FC<StageNavProps> = ({ currentStage, onSelectStage }) => {
  const stages: { id: StageId; number: number; label: string; icon: React.ReactNode }[] = [
    { id: 'request', number: 1, label: 'RFQ Request', icon: <FileText size={16} /> },
    { id: 'quotations', number: 2, label: 'Quotation Upload', icon: <UploadCloud size={16} /> },
    { id: 'live-run', number: 3, label: 'Live Evaluation Run', icon: <PlayCircle size={16} /> },
    { id: 'comparison', number: 4, label: 'Vendor Comparison', icon: <BarChart3 size={16} /> },
    { id: 'what-if', number: 5, label: 'What-If Ranking', icon: <Sliders size={16} /> },
    { id: 'approval', number: 6, label: 'Recommendation & Approvals', icon: <CheckSquare size={16} /> }
  ]

  return (
    <nav className="stage-nav-bar">
      {stages.map((st) => {
        const isActive = currentStage === st.id
        return (
          <button
            key={st.id}
            onClick={() => onSelectStage(st.id)}
            className={`stage-tab ${isActive ? 'active' : ''}`}
          >
            <span className="stage-number">{st.number}</span>
            {st.icon}
            <span>{st.label}</span>
          </button>
        )
      })}
    </nav>
  )
}
