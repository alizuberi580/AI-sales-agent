import React, { useState, useEffect } from 'react'
import { Mail, X, Send, AlertCircle, CheckCircle, Loader, ExternalLink } from 'lucide-react'
import clsx from 'clsx'
import { sendEmail, getGmailStatus, GmailStatus } from '../lib/api'

interface Props {
  isOpen: boolean
  onClose: () => void
  defaultTo?: string
  defaultSubject: string
  defaultBody: string
  companyName: string
}

type SendState = 'idle' | 'sending' | 'sent' | 'error'

export default function SendEmailModal({
  isOpen,
  onClose,
  defaultTo = '',
  defaultSubject,
  defaultBody,
  companyName,
}: Props) {
  const [to, setTo] = useState(defaultTo)
  const [subject, setSubject] = useState(defaultSubject)
  const [body, setBody] = useState(defaultBody)
  const [sendState, setSendState] = useState<SendState>('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const [gmailStatus, setGmailStatus] = useState<GmailStatus | null>(null)
  const [checkingGmail, setCheckingGmail] = useState(true)

  // Reset form when modal opens with new data
  useEffect(() => {
    if (isOpen) {
      setTo(defaultTo)
      setSubject(defaultSubject)
      setBody(defaultBody)
      setSendState('idle')
      setErrorMsg('')
      checkGmail()
    }
  }, [isOpen, defaultSubject, defaultBody])

  const checkGmail = async () => {
    setCheckingGmail(true)
    try {
      const status = await getGmailStatus()
      setGmailStatus(status)
    } catch {
      setGmailStatus({ connected: false, reason: 'Could not reach backend' })
    } finally {
      setCheckingGmail(false)
    }
  }

  const handleSend = async () => {
    if (!to.trim() || !subject.trim() || !body.trim()) return
    setSendState('sending')
    setErrorMsg('')
    try {
      await sendEmail({ to, subject, body, company_name: companyName })
      setSendState('sent')
    } catch (err: any) {
      setSendState('error')
      setErrorMsg(
        err?.response?.data?.detail ||
        err?.message ||
        'Failed to send. Check Gmail is connected.'
      )
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={sendState !== 'sending' ? onClose : undefined}
      />

      {/* Modal */}
      <div className="relative w-full max-w-2xl bg-gray-900 rounded-2xl border border-gray-700 shadow-2xl flex flex-col max-h-[90vh]">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <Mail className="w-5 h-5 text-brand-400" />
            <h2 className="font-semibold text-white">Review & Send Email</h2>
            <span className="badge bg-brand-500/20 text-brand-300 text-xs">{companyName}</span>
          </div>
          <button
            onClick={onClose}
            disabled={sendState === 'sending'}
            className="text-gray-500 hover:text-gray-300 transition-colors disabled:opacity-40"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Gmail Status Banner */}
        {!checkingGmail && (
          <div className={clsx(
            'mx-6 mt-4 rounded-lg px-4 py-2.5 flex items-center gap-2 text-sm',
            gmailStatus?.connected
              ? 'bg-green-900/20 border border-green-800/30 text-green-300'
              : 'bg-yellow-900/20 border border-yellow-800/30 text-yellow-300'
          )}>
            {gmailStatus?.connected ? (
              <>
                <CheckCircle className="w-4 h-4 shrink-0" />
                <span>Gmail connected — sending as <strong>{gmailStatus.sender || 'your account'}</strong></span>
              </>
            ) : (
              <>
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span className="flex-1">
                  Gmail not connected — {gmailStatus?.reason || 'set up Gmail API first'}
                </span>
                <a
                  href="https://console.cloud.google.com/apis/credentials"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 underline text-xs hover:text-yellow-200"
                >
                  Setup guide <ExternalLink className="w-3 h-3" />
                </a>
              </>
            )}
          </div>
        )}

        {/* Human-in-the-Loop Notice */}
        <div className="mx-6 mt-3 bg-blue-900/20 border border-blue-800/30 rounded-lg px-4 py-2.5 text-xs text-blue-300 flex items-start gap-2">
          <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <span>
            <strong>Review before sending.</strong> Edit any field below — this email won't be sent until you click <strong>Confirm & Send</strong>.
          </span>
        </div>

        {/* Form */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">

          {/* To */}
          <div>
            <label className="label">To (recipient email)</label>
            <input
              className="input"
              type="email"
              placeholder="prospect@company.com"
              value={to}
              onChange={e => setTo(e.target.value)}
              disabled={sendState === 'sending' || sendState === 'sent'}
            />
          </div>

          {/* Subject */}
          <div>
            <label className="label">Subject</label>
            <input
              className="input"
              value={subject}
              onChange={e => setSubject(e.target.value)}
              disabled={sendState === 'sending' || sendState === 'sent'}
            />
          </div>

          {/* Body */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="label mb-0">Body</label>
              <span className="text-xs text-gray-600">{body.length} chars</span>
            </div>
            <textarea
              className="input font-mono text-xs leading-relaxed"
              rows={14}
              value={body}
              onChange={e => setBody(e.target.value)}
              disabled={sendState === 'sending' || sendState === 'sent'}
            />
          </div>

          {/* Error */}
          {sendState === 'error' && (
            <div className="bg-red-900/20 border border-red-800/40 rounded-lg px-4 py-3 flex items-start gap-2 text-red-300 text-sm">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Success */}
          {sendState === 'sent' && (
            <div className="bg-green-900/20 border border-green-800/40 rounded-lg px-4 py-3 flex items-center gap-2 text-green-300 text-sm">
              <CheckCircle className="w-4 h-4 shrink-0" />
              <span>Email sent successfully to <strong>{to}</strong></span>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-gray-800 flex items-center justify-between gap-3">
          <button
            onClick={onClose}
            disabled={sendState === 'sending'}
            className="btn-secondary"
          >
            {sendState === 'sent' ? 'Close' : 'Cancel'}
          </button>

          {sendState !== 'sent' && (
            <button
              onClick={handleSend}
              disabled={
                sendState === 'sending' ||
                !gmailStatus?.connected ||
                !to.trim() ||
                !subject.trim() ||
                !body.trim()
              }
              className="btn-primary flex items-center gap-2"
            >
              {sendState === 'sending' ? (
                <>
                  <Loader className="w-4 h-4 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Confirm & Send
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
