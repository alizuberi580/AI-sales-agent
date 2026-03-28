import React from 'react'
import { Building2, MapPin, TrendingUp } from 'lucide-react'
import clsx from 'clsx'
import { LeadResult } from '../lib/api'

interface Props {
  leads: LeadResult[]
  selected: number | null
  onSelect: (idx: number) => void
}

function ScoreBadge({ score }: { score: number }) {
  const color = score >= 70 ? 'bg-green-900/40 text-green-300' :
                score >= 45 ? 'bg-yellow-900/40 text-yellow-300' :
                'bg-red-900/40 text-red-300'
  return (
    <span className={clsx('badge font-bold text-sm', color)}>
      {score}
    </span>
  )
}

export default function LeadsTable({ leads, selected, onSelect }: Props) {
  return (
    <div className="card">
      <h2 className="section-title flex items-center gap-2">
        <Building2 className="w-5 h-5 text-brand-500" />
        Leads ({leads.length})
      </h2>

      <div className="space-y-2">
        {leads.map((lead, idx) => {
          const company = lead.company
          const isSelected = selected === idx
          return (
            <div
              key={company.company_name}
              onClick={() => onSelect(idx)}
              className={clsx(
                'flex items-center justify-between px-4 py-3 rounded-lg cursor-pointer border transition-all',
                isSelected
                  ? 'border-brand-500 bg-brand-500/10'
                  : 'border-gray-800 hover:border-gray-700 hover:bg-gray-800/50'
              )}
            >
              <div className="min-w-0">
                <div className="font-medium text-white text-sm truncate">{company.company_name}</div>
                <div className="flex items-center gap-3 mt-0.5">
                  <span className="flex items-center gap-1 text-xs text-gray-500">
                    <MapPin className="w-3 h-3" />{company.location || 'N/A'}
                  </span>
                  <span className="text-xs text-gray-600">{company.industry}</span>
                  {company.growth_stage && (
                    <span className="flex items-center gap-1 text-xs text-gray-500">
                      <TrendingUp className="w-3 h-3" />{company.growth_stage}
                    </span>
                  )}
                </div>
              </div>
              <ScoreBadge score={company.fit_score ?? 50} />
            </div>
          )
        })}
      </div>
    </div>
  )
}
