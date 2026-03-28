import React from 'react'
import { Search, Database } from 'lucide-react'

interface Props {
  queries: string[]
  source: string
}

export default function QueryViewer({ queries, source }: Props) {
  return (
    <div className="card">
      <h3 className="section-title flex items-center gap-2 text-sm">
        <Search className="w-4 h-4 text-brand-500" />
        Generated Queries
      </h3>
      <div className="space-y-2 mb-3">
        {queries.map((q, i) => (
          <div key={i} className="flex items-center gap-3 text-sm text-gray-300 bg-gray-800/50 px-3 py-2 rounded-lg">
            <span className="text-brand-400 font-mono text-xs">{i + 1}</span>
            <span>{q}</span>
          </div>
        ))}
      </div>
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <Database className="w-3.5 h-3.5" />
        Source: <span className={source === 'web_scraping' ? 'text-green-400' : 'text-yellow-400'}>
          {source === 'web_scraping' ? 'Web Scraping' : 'Fallback Dataset'}
        </span>
      </div>
    </div>
  )
}
