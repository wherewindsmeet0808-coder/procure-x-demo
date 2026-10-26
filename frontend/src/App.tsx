import React, { useState, useEffect } from 'react'
import { Header } from './components/Header'
import { StageNav, StageId } from './components/StageNav'
import { RequestStage } from './components/stages/RequestStage'
import { QuotationStage } from './components/stages/QuotationStage'
import { LiveRunStage } from './components/stages/LiveRunStage'
import { ComparisonStage } from './components/stages/ComparisonStage'
import { WhatIfStage } from './components/stages/WhatIfStage'
import { ApprovalStage } from './components/stages/ApprovalStage'
import { SystemStatus, RFQRequest, Vendor, Quotation } from './types/procurement'
import { fetchSystemStatus, fetchRFQs, fetchVendors, fetchQuotations, resetDemoData } from './services/api'

export function App() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [rfqs, setRfqs] = useState<RFQRequest[]>([])
  const [selectedRfqId, setSelectedRfqId] = useState<string>('')
  const [vendors, setVendors] = useState<Vendor[]>([])
  const [quotations, setQuotations] = useState<Quotation[]>([])
  const [currentStage, setCurrentStage] = useState<StageId>('request')
  const [isResetting, setIsResetting] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    initApp()
  }, [])

  const initApp = async () => {
    try {
      setLoading(true)
      const [sysStatus, rfqList, vendorList] = await Promise.all([
        fetchSystemStatus(),
        fetchRFQs(),
        fetchVendors()
      ])
      setStatus(sysStatus)
      setRfqs(rfqList)
      setVendors(vendorList)

      const activeId = rfqList.length > 0 ? rfqList[0].id : ''
      setSelectedRfqId(activeId)

      if (activeId) {
        const quotes = await fetchQuotations(activeId)
        setQuotations(quotes)
      }
      setLoading(false)
    } catch (err) {
      console.error('App init error:', err)
      setLoading(false)
    }
  }

  const handleSelectRfq = async (id: string) => {
    setSelectedRfqId(id)
    try {
      const quotes = await fetchQuotations(id)
      setQuotations(quotes)
    } catch (err) {
      console.error('Fetch quotations error:', err)
    }
  }

  const handleResetDemo = async () => {
    try {
      setIsResetting(true)
      await resetDemoData()
      await initApp()
      setIsResetting(false)
    } catch (err: any) {
      setIsResetting(false)
      alert(err.message || 'Reset failed')
    }
  }

  const handleRefreshCurrentData = async () => {
    if (!selectedRfqId) return
    try {
      const [rfqList, quotes] = await Promise.all([
        fetchRFQs(),
        fetchQuotations(selectedRfqId)
      ])
      setRfqs(rfqList)
      setQuotations(quotes)
    } catch (err) {
      console.error(err)
    }
  }

  const currentRfq = rfqs.find(r => r.id === selectedRfqId) || (rfqs.length > 0 ? rfqs[0] : null)

  return (
    <div className="app-container">
      {/* Top Header */}
      <Header
        status={status}
        rfqs={rfqs}
        selectedRfqId={selectedRfqId}
        onSelectRfq={handleSelectRfq}
        onResetDemo={handleResetDemo}
        isResetting={isResetting}
      />

      {/* Stage Stepper Navigation Bar */}
      <StageNav
        currentStage={currentStage}
        onSelectStage={setCurrentStage}
      />

      {/* Main Workspace Body */}
      <main className="main-content">
        {loading ? (
          <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
            <p style={{ color: 'var(--text-muted)' }}>Connecting to ProcureSense backend & loading state...</p>
          </div>
        ) : (
          <>
            {currentStage === 'request' && (
              <RequestStage
                rfq={currentRfq}
                onRefresh={handleRefreshCurrentData}
                onAdvanceToQuotations={() => setCurrentStage('quotations')}
              />
            )}

            {currentStage === 'quotations' && (
              <QuotationStage
                rfq={currentRfq}
                quotations={quotations}
                vendors={vendors}
                onRefresh={handleRefreshCurrentData}
                onAdvanceToLiveRun={() => setCurrentStage('live-run')}
              />
            )}

            {currentStage === 'live-run' && (
              <LiveRunStage
                rfq={currentRfq}
                onAdvanceToComparison={() => setCurrentStage('comparison')}
              />
            )}

            {currentStage === 'comparison' && (
              <ComparisonStage
                rfq={currentRfq}
                onAdvanceToWhatIf={() => setCurrentStage('what-if')}
              />
            )}

            {currentStage === 'what-if' && (
              <WhatIfStage
                rfq={currentRfq}
                onAdvanceToApproval={() => setCurrentStage('approval')}
              />
            )}

            {currentStage === 'approval' && (
              <ApprovalStage
                rfq={currentRfq}
                onRefresh={handleRefreshCurrentData}
              />
            )}
          </>
        )}
      </main>
    </div>
  )
}

export default App
