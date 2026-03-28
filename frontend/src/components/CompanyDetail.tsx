import React, { useState } from 'react'
import { Building2, Search, Zap, Mail, CheckSquare, RefreshCw, Copy, Check, Send } from 'lucide-react'
import clsx from 'clsx'
import { LeadResult } from '../lib/api'
import SendEmailModal from './SendEmailModal'

interface Props {
  lead: LeadResult
}

type Tab = 'overview' | 'research' | 'signals' | 'outreach' | 'qa' | 'followup'

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <button onClick={copy} className="btn-secondary py-1 px-2 text-xs flex items-center gap-1">
      {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

function SignalStrength({ strength }: { strength: string }) {
  const color = strength === 'high' ? 'text-green-400' : strength === 'medium' ? 'text-yellow-400' : 'text-red-400'
  return <span className={clsx('text-xs font-bold uppercase', color)}>{strength}</span>
}

const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
  { key: 'overview', label: 'Overview', icon: <Building2 className="w-4 h-4" /> },
  { key: 'research', label: 'Research', icon: <Search className="w-4 h-4" /> },
  { key: 'signals', label: 'Signals', icon: <Zap className="w-4 h-4" /> },
  { key: 'outreach', label: 'Outreach', icon: <Mail className="w-4 h-4" /> },
  { key: 'qa', label: 'QA', icon: <CheckSquare className="w-4 h-4" /> },
  { key: 'followup', label: 'Follow-up', icon: <RefreshCw className="w-4 h-4" /> },
]

export default function CompanyDetail({ lead }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [sendModalOpen, setSendModalOpen] = useState(false)
  const { company, research, signals, personalization, outreach, qa, followup } = lead

  return (
    <div className="card flex flex-col gap-4">
      <SendEmailModal
        isOpen={sendModalOpen}
        onClose={() => setSendModalOpen(false)}
        defaultSubject={outreach?.email?.subject || ''}
        defaultBody={outreach?.email?.body || ''}
        companyName={company.company_name}
      />
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">{company.company_name}</h2>
          <p className="text-sm text-gray-400 mt-0.5">{company.industry} · {company.location}</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-brand-400">{company.fit_score ?? 50}</div>
          <div className="text-xs text-gray-500">fit score</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 flex-wrap">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={clsx('tab flex items-center gap-1.5 text-xs', activeTab === tab.key ? 'tab-active' : 'tab-inactive')}
          >
            {tab.icon}{tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="text-sm space-y-3">

        {/* OVERVIEW */}
        {activeTab === 'overview' && (
          <div className="space-y-4">
            <p className="text-gray-300">{company.description}</p>
            <div className="grid grid-cols-2 gap-3">
              {[
                ['Size', company.company_size],
                ['Revenue', company.revenue_range],
                ['Stage', company.growth_stage],
              ].map(([k, v]) => v ? (
                <div key={k} className="bg-gray-800/50 rounded-lg p-3">
                  <div className="text-xs text-gray-500">{k}</div>
                  <div className="text-white font-medium mt-0.5">{v}</div>
                </div>
              ) : null)}
            </div>
            {Array.isArray(company.tech_stack) && company.tech_stack.length > 0 && (
              <div>
                <div className="text-xs text-gray-500 mb-2">Tech Stack</div>
                <div className="flex flex-wrap gap-1.5">
                  {company.tech_stack.map(t => (
                    <span key={t} className="badge bg-blue-900/30 text-blue-300">{t}</span>
                  ))}
                </div>
              </div>
            )}
            {personalization.hook && (
              <div className="bg-brand-500/10 border border-brand-500/20 rounded-lg p-3">
                <div className="text-xs text-brand-400 font-medium mb-1">Personalized Hook</div>
                <p className="text-gray-200">{personalization.hook}</p>
              </div>
            )}
          </div>
        )}

        {/* RESEARCH */}
        {activeTab === 'research' && (
          <div className="space-y-3">
            {research.research_summary && (
              <div className="bg-gray-800/50 rounded-lg p-3">
                <div className="text-xs text-gray-500 mb-1">Summary</div>
                <p className="text-gray-200">{research.research_summary}</p>
              </div>
            )}
            {research.business_model && (
              <div>
                <div className="text-xs text-gray-500 mb-1">Business Model</div>
                <p className="text-gray-300">{research.business_model}</p>
              </div>
            )}
            {Array.isArray(research.key_challenges) && (
              <div>
                <div className="text-xs text-gray-500 mb-2">Key Challenges</div>
                <ul className="space-y-1">
                  {research.key_challenges.map((c: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-gray-300">
                      <span className="text-red-400 mt-0.5">•</span>{c}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {Array.isArray(research.buying_triggers) && (
              <div>
                <div className="text-xs text-gray-500 mb-2">Buying Triggers</div>
                <ul className="space-y-1">
                  {research.buying_triggers.map((t: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-green-300">
                      <span className="mt-0.5">⚡</span>{t}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* SIGNALS */}
        {activeTab === 'signals' && (
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="text-xs text-gray-500">Overall Signal:</div>
              <SignalStrength strength={signals.overall_signal_strength ?? 'medium'} />
            </div>
            {signals.recommended_action && (
              <div className="bg-green-900/20 border border-green-800/30 rounded-lg p-3 text-green-300 text-sm">
                {signals.recommended_action} · <span className="text-gray-400">{signals.timing}</span>
              </div>
            )}
            {Array.isArray(signals.signals) && signals.signals.map((s: any, i: number) => (
              <div key={i} className="bg-gray-800/50 rounded-lg p-3 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="badge bg-gray-700 text-gray-300 capitalize">{s.type}</span>
                  <SignalStrength strength={s.strength} />
                </div>
                <p className="text-gray-200">{s.signal}</p>
                <p className="text-xs text-gray-500">{s.relevance}</p>
              </div>
            ))}
          </div>
        )}

        {/* OUTREACH */}
        {activeTab === 'outreach' && (
          <div className="space-y-4">
            {/* Email */}
            {outreach.email && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Cold Email</div>
                  <div className="flex items-center gap-2">
                    <CopyButton text={`Subject: ${outreach.email.subject}\n\n${outreach.email.body}`} />
                    <button
                      onClick={() => setSendModalOpen(true)}
                      className="btn-primary py-1 px-3 text-xs flex items-center gap-1.5"
                    >
                      <Send className="w-3 h-3" />
                      Send Email
                    </button>
                  </div>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-3 space-y-2">
                  <div className="text-xs text-gray-500">Subject</div>
                  <div className="font-medium text-white">{outreach.email.subject}</div>
                  <div className="border-t border-gray-700 pt-2 text-gray-300 whitespace-pre-wrap leading-relaxed">
                    {outreach.email.body}
                  </div>
                </div>
              </div>
            )}

            {/* LinkedIn */}
            {outreach.linkedin && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">LinkedIn Message</div>
                  <CopyButton text={outreach.linkedin.message} />
                </div>
                <div className="bg-blue-900/20 border border-blue-800/30 rounded-lg p-3 text-gray-300">
                  {outreach.linkedin.message}
                </div>
              </div>
            )}

            {/* WhatsApp */}
            {outreach.whatsapp && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">WhatsApp</div>
                  <CopyButton text={outreach.whatsapp.message} />
                </div>
                <div className="bg-green-900/20 border border-green-800/30 rounded-lg p-3 text-gray-300">
                  {outreach.whatsapp.message}
                </div>
              </div>
            )}
          </div>
        )}

        {/* QA */}
        {activeTab === 'qa' && (
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="text-xs text-gray-500">Email Score:</div>
              <div className={clsx('text-2xl font-bold', qa.score >= 70 ? 'text-green-400' : qa.score >= 50 ? 'text-yellow-400' : 'text-red-400')}>
                {qa.score}/100
              </div>
            </div>
            {Array.isArray(qa.issues) && qa.issues.length > 0 && (
              <div>
                <div className="text-xs text-red-400 font-medium mb-2">Issues</div>
                <ul className="space-y-1">
                  {qa.issues.map((issue: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-gray-300 text-xs">
                      <span className="text-red-400">⚠</span>{issue}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {Array.isArray(qa.strengths) && qa.strengths.length > 0 && (
              <div>
                <div className="text-xs text-green-400 font-medium mb-2">Strengths</div>
                <ul className="space-y-1">
                  {qa.strengths.map((s: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-gray-300 text-xs">
                      <span className="text-green-400">✓</span>{s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {qa.improved_email && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Improved Email</div>
                  <CopyButton text={`Subject: ${qa.improved_subject}\n\n${qa.improved_email}`} />
                </div>
                <div className="bg-gray-800/50 rounded-lg p-3 space-y-2">
                  <div className="font-medium text-white">{qa.improved_subject}</div>
                  <div className="border-t border-gray-700 pt-2 text-gray-300 whitespace-pre-wrap text-xs leading-relaxed">
                    {qa.improved_email}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* FOLLOWUP */}
        {activeTab === 'followup' && (
          <div className="space-y-3">
            {Array.isArray(followup.sequence) && followup.sequence.map((touch: any) => (
              <div key={touch.touch} className="bg-gray-800/50 rounded-lg p-3 space-y-2">
                <div className="flex items-center gap-3">
                  <span className="badge bg-brand-500/20 text-brand-300 font-bold">Touch {touch.touch}</span>
                  <span className="text-xs text-gray-500">Day {touch.day}</span>
                  <span className="badge bg-gray-700 text-gray-300 capitalize">{touch.channel}</span>
                </div>
                {touch.subject && (
                  <div className="text-xs text-gray-500">Subject: <span className="text-gray-300">{touch.subject}</span></div>
                )}
                <p className="text-gray-300 text-xs whitespace-pre-wrap leading-relaxed">{touch.message}</p>
                <div className="text-xs text-gray-600">Goal: {touch.goal}</div>
              </div>
            ))}
            {followup.recommended_pause_after && (
              <div className="text-xs text-gray-500 text-center pt-2">
                {followup.recommended_pause_after}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
