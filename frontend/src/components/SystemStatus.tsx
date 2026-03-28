import React, { useEffect, useState } from 'react'
import { CheckCircle, XCircle, Loader } from 'lucide-react'
import axios from 'axios'
import clsx from 'clsx'

interface HealthData {
  status: string
  llm: { provider: string; model: string; key_set: boolean }
  rag: { backend: string; pinecone_configured: boolean }
  gmail: { connected: boolean; sender?: string }
}

function Dot({ ok, loading, label }: { ok: boolean; loading: boolean; label: string }) {
  return (
    <div className="flex items-center gap-1.5 text-xs">
      {loading ? (
        <Loader className="w-3 h-3 text-gray-500 animate-spin" />
      ) : ok ? (
        <CheckCircle className="w-3 h-3 text-green-400" />
      ) : (
        <XCircle className="w-3 h-3 text-red-400" />
      )}
      <span className={clsx(loading ? 'text-gray-500' : ok ? 'text-green-300' : 'text-red-300')}>
        {label}
      </span>
    </div>
  )
}

export default function SystemStatus() {
  const [health, setHealth] = useState<HealthData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('/health', { timeout: 5000 })
      .then(r => setHealth(r.data))
      .catch(() => setHealth(null))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="flex items-center gap-4 px-3 py-1.5 bg-gray-800/50 rounded-lg border border-gray-700/50">
      <Dot loading={loading} ok={!!health?.llm?.key_set} label={health?.llm?.model || 'Groq'} />
      <div className="w-px h-3 bg-gray-700" />
      <Dot loading={loading} ok={health?.rag?.backend === 'pinecone'} label={health?.rag?.backend === 'pinecone' ? 'Pinecone' : 'RAG (TF-IDF)'} />
      <div className="w-px h-3 bg-gray-700" />
      <Dot loading={loading} ok={!!health?.gmail?.connected} label={health?.gmail?.connected ? 'Gmail' : 'Gmail (off)'} />
    </div>
  )
}
