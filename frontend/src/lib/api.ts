import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000,
})

export interface ICPData {
  industry: string
  business_type: string
  location: string
  company_size: string
  revenue_range: string
  growth_stage: string
  pain_points: string[]
  tech_stack: string[]
  product_offering: string
  value_proposition: string
}

export interface Company {
  company_name: string
  description: string
  industry: string
  location: string
  company_size: string
  revenue_range: string
  growth_stage: string
  tech_stack: string[]
  fit_score: number
}

export interface PipelineResult {
  status: string
  icp: ICPData
  queries: string[]
  pipeline_source: string
  total_leads: number
  leads: LeadResult[]
  steps_completed: string[]
}

export interface LeadResult {
  company: Company
  research: Record<string, any>
  signals: Record<string, any>
  personalization: Record<string, any>
  outreach: Record<string, any>
  qa: Record<string, any>
  followup: Record<string, any>
}

export interface GmailStatus {
  connected: boolean
  sender?: string
  reason?: string
}

export interface SendEmailPayload {
  to: string
  subject: string
  body: string
  company_name?: string
}

export const runPipeline = async (icp: ICPData): Promise<PipelineResult> => {
  const { data } = await api.post('/pipeline', icp)
  return data
}

export const formatICP = async (icp: ICPData) => {
  const { data } = await api.post('/icp', icp)
  return data
}

export const getGmailStatus = async (): Promise<GmailStatus> => {
  const { data } = await api.get('/gmail/status')
  return data.data
}

export const sendEmail = async (payload: SendEmailPayload) => {
  const { data } = await api.post('/gmail/send', payload)
  return data
}

export default api
