import React, { useState } from 'react'
import { Bot, AlertCircle, Zap, Users, Mail, GitBranch, BarChart2 } from 'lucide-react'
import ICPBuilder from './components/ICPBuilder'
import PipelineStatus from './components/PipelineStatus'
import LeadsTable from './components/LeadsTable'
import CompanyDetail from './components/CompanyDetail'
import QueryViewer from './components/QueryViewer'
import SystemStatus from './components/SystemStatus'
import { runPipeline, ICPData, PipelineResult } from './lib/api'

const PIPELINE_STEPS = ['icp', 'queries', 'leads', 'research', 'signals', 'personalization', 'outreach', 'qa', 'followup']

function StatCard({ value, label, color }: { value: string | number; label: string; color: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-4 px-2">
      <div className={`text-3xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-1 text-center">{label}</div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="card flex flex-col items-center justify-center py-24 text-center gap-4">
      <div className="w-16 h-16 rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center">
        <Bot className="w-8 h-8 text-brand-400" />
      </div>
      <div>
        <p className="text-white font-semibold">No leads yet</p>
        <p className="text-gray-500 text-sm mt-1">Fill in your ICP and click<br /><span className="text-brand-400">Run AI GTM Pipeline</span></p>
      </div>
      <div className="grid grid-cols-2 gap-2 mt-2 w-full max-w-xs">
        {[
          { icon: <Zap className="w-4 h-4" />, label: '10 AI Agents' },
          { icon: <Users className="w-4 h-4" />, label: 'Lead Scoring' },
          { icon: <Mail className="w-4 h-4" />, label: 'Cold Emails' },
          { icon: <GitBranch className="w-4 h-4" />, label: 'Follow-ups' },
        ].map(f => (
          <div key={f.label} className="flex items-center gap-2 bg-gray-800/50 rounded-lg px-3 py-2 text-xs text-gray-400">
            {f.icon}{f.label}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function App() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<PipelineResult | null>(null)
  const [selectedLead, setSelectedLead] = useState<number | null>(null)
  const [completedSteps, setCompletedSteps] = useState<string[]>([])

  const handleRun = async (icp: ICPData) => {
    setLoading(true)
    setError(null)
    setResult(null)
    setSelectedLead(null)
    setCompletedSteps([])

    let stepIdx = 0
    const interval = setInterval(() => {
      if (stepIdx < PIPELINE_STEPS.length) {
        setCompletedSteps(prev => [...prev, PIPELINE_STEPS[stepIdx++]])
      } else {
        clearInterval(interval)
      }
    }, 600)

    try {
      const data = await runPipeline(icp)
      clearInterval(interval)
      setCompletedSteps(data.steps_completed || PIPELINE_STEPS)
      setResult(data)
      if (data.leads.length > 0) setSelectedLead(0)
    } catch (err: any) {
      clearInterval(interval)
      setError(err?.response?.data?.detail || err?.message || 'Pipeline failed.')
    } finally {
      setLoading(false)
    }
  }

  const selectedLeadData = result && selectedLead !== null ? result.leads[selectedLead] : null
  const highFit = result ? result.leads.filter(l => (l.company.fit_score ?? 0) >= 70).length : 0
  const emailsGen = result ? result.leads.filter(l => l.outreach?.email?.subject).length : 0
  const sequencesGen = result ? result.leads.filter(l => Array.isArray(l.followup?.sequence) && l.followup.sequence.length > 0).length : 0

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">

      {/* ── Header ── */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur sticky top-0 z-20">
        <div className="max-w-screen-2xl mx-auto px-6 h-14 flex items-center justify-between gap-4">

          {/* Logo */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center shadow-lg shadow-brand-500/30">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-bold text-white text-base">AI Sales Co-Pilot</span>
              <span className="text-gray-600 text-xs hidden sm:block">Multi-Agent GTM System</span>
            </div>
          </div>

          {/* Center badges */}
          <div className="flex items-center gap-2">
            <span className="badge bg-blue-900/30 text-blue-300 text-xs">Groq LLM</span>
            <span className="badge bg-purple-900/30 text-purple-300 text-xs">Pinecone RAG</span>
            <span className="badge bg-green-900/30 text-green-300 text-xs">Gmail Send</span>
          </div>

          {/* System status */}
          <SystemStatus />
        </div>
      </header>

      <div className="max-w-screen-2xl mx-auto px-6 py-6 flex-1 w-full">

        {/* ── Error Banner ── */}
        {error && (
          <div className="mb-5 bg-red-900/20 border border-red-800/40 rounded-xl p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            <div className="min-w-0">
              <div className="text-red-300 font-medium text-sm">Pipeline Error</div>
              <div className="text-red-400/80 text-sm mt-0.5 break-words">{error}</div>
              <div className="text-gray-500 text-xs mt-1.5">
                Ensure the backend is running on port 8002:&nbsp;
                <code className="text-gray-400">cd backend &amp;&amp; uvicorn app.main:app --reload --port 8002</code>
              </div>
            </div>
          </div>
        )}

        {/* ── Stats Bar (after results) ── */}
        {result && (
          <div className="mb-5 card">
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 divide-x divide-gray-800">
              <StatCard value={result.total_leads} label="Total Leads" color="text-brand-400" />
              <StatCard value={highFit} label="High Fit (≥70)" color="text-green-400" />
              <StatCard value={emailsGen} label="Emails Written" color="text-purple-400" />
              <StatCard value={sequencesGen} label="Follow-up Seqs" color="text-yellow-400" />
              <StatCard
                value={result.leads.filter(l => l.signals?.overall_signal_strength === 'high').length}
                label="Strong Signals"
                color="text-orange-400"
              />
              <StatCard
                value={result.pipeline_source === 'web_scraping' ? 'Live' : 'Dataset'}
                label="Lead Source"
                color="text-sky-400"
              />
            </div>
          </div>
        )}

        {/* ── Main 3-column Layout ── */}
        <div className="grid grid-cols-12 gap-5">

          {/* LEFT — ICP Builder + Pipeline Status */}
          <div className="col-span-12 lg:col-span-3 space-y-5">
            <ICPBuilder onRun={handleRun} loading={loading} />
            {(loading || result) && (
              <PipelineStatus completedSteps={completedSteps} loading={loading} />
            )}
          </div>

          {/* CENTER — Queries + Leads */}
          <div className="col-span-12 lg:col-span-3 space-y-5">
            {result && (
              <>
                <QueryViewer queries={result.queries || []} source={result.pipeline_source} />
                <LeadsTable leads={result.leads} selected={selectedLead} onSelect={setSelectedLead} />
              </>
            )}
            {!result && !loading && <EmptyState />}
            {loading && (
              <div className="card flex flex-col items-center justify-center py-24 text-center gap-4">
                <div className="relative w-14 h-14">
                  <div className="absolute inset-0 rounded-full border-2 border-brand-500/20" />
                  <div className="absolute inset-0 rounded-full border-2 border-t-brand-500 animate-spin" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Bot className="w-6 h-6 text-brand-400" />
                  </div>
                </div>
                <div>
                  <p className="text-white font-medium text-sm">Agents working...</p>
                  <p className="text-gray-500 text-xs mt-1">Running all 10 agents in parallel</p>
                </div>
              </div>
            )}
          </div>

          {/* RIGHT — Company Detail */}
          <div className="col-span-12 lg:col-span-6">
            {selectedLeadData ? (
              <CompanyDetail lead={selectedLeadData} />
            ) : (
              <div className="card flex flex-col items-center justify-center py-32 text-center gap-3">
                <BarChart2 className="w-14 h-14 text-gray-800" />
                <p className="text-gray-600 text-sm">
                  {result ? 'Select a lead from the list to view full details' : 'Run the pipeline to see results here'}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Footer ── */}
      <footer className="border-t border-gray-800 bg-gray-900/40 mt-6">
        <div className="max-w-screen-2xl mx-auto px-6 h-10 flex items-center justify-between text-xs text-gray-600">
          <span>AI Sales Co-Pilot — Multi-Agent GTM System</span>
          <span>Groq · Pinecone · Gmail · React · FastAPI</span>
        </div>
      </footer>
    </div>
  )
}
