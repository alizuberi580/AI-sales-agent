import React from 'react'
import { CheckCircle, Circle, Loader } from 'lucide-react'
import clsx from 'clsx'

const STEPS = [
  { key: 'icp', label: 'ICP Formatter' },
  { key: 'queries', label: 'Query Generator' },
  { key: 'leads', label: 'Lead Generator' },
  { key: 'research', label: 'Research Agent (RAG)' },
  { key: 'signals', label: 'Signal Detection' },
  { key: 'personalization', label: 'Personalization' },
  { key: 'outreach', label: 'Outreach Writer' },
  { key: 'qa', label: 'QA Agent' },
  { key: 'followup', label: 'Follow-up Sequencer' },
]

interface Props {
  completedSteps: string[]
  loading: boolean
}

export default function PipelineStatus({ completedSteps, loading }: Props) {
  const currentIdx = STEPS.findIndex(s => !completedSteps.includes(s.key))

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Pipeline Status</h3>
      <div className="space-y-2">
        {STEPS.map((step, idx) => {
          const done = completedSteps.includes(step.key)
          const active = loading && idx === currentIdx

          return (
            <div key={step.key} className={clsx(
              'flex items-center gap-3 text-sm px-3 py-2 rounded-lg transition-colors',
              done && 'bg-green-900/20 text-green-300',
              active && 'bg-brand-500/20 text-brand-300',
              !done && !active && 'text-gray-600'
            )}>
              {done ? (
                <CheckCircle className="w-4 h-4 text-green-400 shrink-0" />
              ) : active ? (
                <Loader className="w-4 h-4 text-brand-400 animate-spin shrink-0" />
              ) : (
                <Circle className="w-4 h-4 shrink-0" />
              )}
              <span className="font-medium">{idx + 1}. {step.label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
