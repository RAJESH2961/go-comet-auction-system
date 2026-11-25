import { useEffect, useState } from 'react'
import { Loader2, X } from 'lucide-react'

export const fmt = (n) =>
  n == null ? '—' : `₹${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`

export const fmtDT = (s) =>
  s ? new Date(s).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }) : '—'

const STATUS_STYLES = {
  UPCOMING: 'bg-blue-50 text-blue-700 ring-blue-200',
  ACTIVE: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  CLOSED: 'bg-slate-100 text-slate-600 ring-slate-300',
  FORCE_CLOSED: 'bg-amber-50 text-amber-700 ring-amber-200',
}

export function StatusBadge({ status }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ${STATUS_STYLES[status] || STATUS_STYLES.CLOSED}`}>
      {status === 'ACTIVE' && <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />}
      {status?.replace('_', ' ')}
    </span>
  )
}

export function StatCard({ icon: Icon, label, value, accent = 'text-brand-600 bg-brand-50' }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        <div className={`rounded-lg p-2 ${accent}`}><Icon size={18} /></div>
      </div>
      <p className="mt-2 text-2xl font-semibold tracking-tight">{value}</p>
    </div>
  )
}

export function Countdown({ target, onExpire }) {
  const [left, setLeft] = useState(() => Math.max(0, new Date(target) - Date.now()))
  useEffect(() => {
    const t = setInterval(() => {
      const v = Math.max(0, new Date(target) - Date.now())
      setLeft(v)
      if (v === 0) onExpire?.()
    }, 1000)
    return () => clearInterval(t)
  }, [target])
  const s = Math.floor(left / 1000)
  const h = String(Math.floor(s / 3600)).padStart(2, '0')
  const m = String(Math.floor((s % 3600) / 60)).padStart(2, '0')
  const sec = String(s % 60).padStart(2, '0')
  const urgent = left < 10 * 60 * 1000
  return (
    <span className={`font-mono tabular-nums ${urgent ? 'text-red-600 font-semibold' : ''}`}>
      {h}:{m}:{sec}
    </span>
  )
}

export function Spinner({ text = 'Loading…' }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-slate-500">
      <Loader2 className="animate-spin" size={20} /> {text}
    </div>
  )
}

export function EmptyState({ title, hint }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white py-14 text-center">
      <p className="font-medium text-slate-600">{title}</p>
      {hint && <p className="mt-1 text-sm text-slate-400">{hint}</p>}
    </div>
  )
}

export function Toast({ toast, onClose }) {
  if (!toast) return null
  const colors = {
    success: 'bg-emerald-600',
    error: 'bg-red-600',
    info: 'bg-brand-600',
  }
  return (
    <div className={`fixed bottom-5 right-5 z-50 flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium text-white shadow-lg ${colors[toast.type] || colors.info}`}>
      {toast.message}
      <button onClick={onClose}><X size={16} /></button>
    </div>
  )
}

export function Modal({ open, title, children, onClose }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/40 p-4" onClick={onClose}>
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X size={20} /></button>
        </div>
        {children}
      </div>
    </div>
  )
}
