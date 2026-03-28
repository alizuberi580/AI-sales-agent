import React, { useState } from 'react'
import { Zap, Plus, X } from 'lucide-react'
import { ICPData } from '../lib/api'

const DEFAULT_ICP: ICPData = {
  industry: 'SaaS',
  business_type: 'B2B',
  location: 'Pakistan',
  company_size: '51-200',
  revenue_range: '$1M-$10M',
  growth_stage: 'Series A',
  pain_points: ['manual sales processes', 'poor lead quality', 'low conversion rates'],
  tech_stack: ['cloud', 'CRM', 'APIs'],
  product_offering: 'AI-powered sales automation and lead generation platform',
  value_proposition: 'Help B2B companies 3x their pipeline with AI-driven prospecting and personalized outreach',
}

interface Props {
  onRun: (icp: ICPData) => void
  loading: boolean
}

export default function ICPBuilder({ onRun, loading }: Props) {
  const [icp, setIcp] = useState<ICPData>(DEFAULT_ICP)
  const [painInput, setPainInput] = useState('')
  const [techInput, setTechInput] = useState('')

  const set = (field: keyof ICPData, value: any) =>
    setIcp(prev => ({ ...prev, [field]: value }))

  const addTag = (field: 'pain_points' | 'tech_stack', input: string, setInput: (v: string) => void) => {
    const val = input.trim()
    if (!val) return
    const current = icp[field] as string[]
    if (!current.includes(val)) set(field, [...current, val])
    setInput('')
  }

  const removeTag = (field: 'pain_points' | 'tech_stack', tag: string) => {
    set(field, (icp[field] as string[]).filter(t => t !== tag))
  }

  return (
    <div className="card">
      <h2 className="section-title flex items-center gap-2">
        <Zap className="w-5 h-5 text-brand-500" />
        ICP Builder
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Industry */}
        <div>
          <label className="label">Industry</label>
          <select className="input" value={icp.industry} onChange={e => set('industry', e.target.value)}>
            {['SaaS', 'FinTech SaaS', 'HealthTech SaaS', 'E-commerce', 'E-commerce SaaS', 'Logistics SaaS', 'AI SaaS', 'RetailTech'].map(o => (
              <option key={o}>{o}</option>
            ))}
          </select>
        </div>

        {/* Business Type */}
        <div>
          <label className="label">Business Type</label>
          <select className="input" value={icp.business_type} onChange={e => set('business_type', e.target.value)}>
            {['B2B', 'B2C', 'Both'].map(o => <option key={o}>{o}</option>)}
          </select>
        </div>

        {/* Location */}
        <div>
          <label className="label">Target Location</label>
          <select className="input" value={icp.location} onChange={e => set('location', e.target.value)}>
            {['Pakistan', 'UAE', 'Saudi Arabia', 'Egypt', 'MENA', 'South Asia', 'Global'].map(o => (
              <option key={o}>{o}</option>
            ))}
          </select>
        </div>

        {/* Company Size */}
        <div>
          <label className="label">Company Size</label>
          <select className="input" value={icp.company_size} onChange={e => set('company_size', e.target.value)}>
            {['1-10', '11-50', '51-200', '201-500', '501-1000', '1000+'].map(o => (
              <option key={o}>{o}</option>
            ))}
          </select>
        </div>

        {/* Revenue Range */}
        <div>
          <label className="label">Revenue Range</label>
          <select className="input" value={icp.revenue_range} onChange={e => set('revenue_range', e.target.value)}>
            {['$100K-$500K', '$500K-$1M', '$1M-$5M', '$5M-$20M', '$20M-$50M', '$50M+'].map(o => (
              <option key={o}>{o}</option>
            ))}
          </select>
        </div>

        {/* Growth Stage */}
        <div>
          <label className="label">Growth Stage</label>
          <select className="input" value={icp.growth_stage} onChange={e => set('growth_stage', e.target.value)}>
            {['Seed', 'Series A', 'Series B', 'Series C', 'Growth', 'Public'].map(o => (
              <option key={o}>{o}</option>
            ))}
          </select>
        </div>

        {/* Product Offering */}
        <div className="md:col-span-2">
          <label className="label">Product Offering</label>
          <input className="input" value={icp.product_offering} onChange={e => set('product_offering', e.target.value)} />
        </div>

        {/* Value Proposition */}
        <div className="md:col-span-2">
          <label className="label">Value Proposition</label>
          <textarea className="input" rows={2} value={icp.value_proposition} onChange={e => set('value_proposition', e.target.value)} />
        </div>

        {/* Pain Points */}
        <div className="md:col-span-2">
          <label className="label">Pain Points</label>
          <div className="flex gap-2 mb-2">
            <input
              className="input"
              placeholder="Add a pain point..."
              value={painInput}
              onChange={e => setPainInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && addTag('pain_points', painInput, setPainInput)}
            />
            <button className="btn-secondary px-3" onClick={() => addTag('pain_points', painInput, setPainInput)}>
              <Plus className="w-4 h-4" />
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {icp.pain_points.map(tag => (
              <span key={tag} className="badge bg-red-900/40 text-red-300 gap-1">
                {tag}
                <button onClick={() => removeTag('pain_points', tag)}><X className="w-3 h-3" /></button>
              </span>
            ))}
          </div>
        </div>

        {/* Tech Stack */}
        <div className="md:col-span-2">
          <label className="label">Tech Stack</label>
          <div className="flex gap-2 mb-2">
            <input
              className="input"
              placeholder="Add a technology..."
              value={techInput}
              onChange={e => setTechInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && addTag('tech_stack', techInput, setTechInput)}
            />
            <button className="btn-secondary px-3" onClick={() => addTag('tech_stack', techInput, setTechInput)}>
              <Plus className="w-4 h-4" />
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {icp.tech_stack.map(tag => (
              <span key={tag} className="badge bg-blue-900/40 text-blue-300 gap-1">
                {tag}
                <button onClick={() => removeTag('tech_stack', tag)}><X className="w-3 h-3" /></button>
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-6">
        <button
          className="btn-primary w-full text-base py-3 flex items-center justify-center gap-2"
          onClick={() => onRun(icp)}
          disabled={loading}
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Running AI Pipeline...
            </>
          ) : (
            <>
              <Zap className="w-5 h-5" />
              Run AI GTM Pipeline
            </>
          )}
        </button>
      </div>
    </div>
  )
}
