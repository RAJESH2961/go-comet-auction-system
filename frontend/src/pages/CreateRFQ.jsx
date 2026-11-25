import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const input = 'w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100'
const label = 'mb-1 block text-sm font-medium text-slate-700'

function toISO(local) {
  return local ? new Date(local).toISOString() : null
}

export default function CreateRFQ() {
  const nav = useNavigate()
  const [form, setForm] = useState({
    name: '', reference_id: '', description: '',
    pickup_location: '', destination_location: '', service_date: '',
    bid_start_time: '', bid_close_time: '', forced_close_time: '',
    trigger_window_minutes: 10, extension_duration_minutes: 5,
    trigger_type: 'BID_RECEIVED',
  })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setError(''); setBusy(true)
    try {
      const { data } = await api.post('/rfqs', {
        name: form.name,
        reference_id: form.reference_id,
        description: form.description || null,
        pickup_location: form.pickup_location || null,
        destination_location: form.destination_location || null,
        service_date: toISO(form.service_date),
        bid_start_time: toISO(form.bid_start_time),
        bid_close_time: toISO(form.bid_close_time),
        forced_close_time: toISO(form.forced_close_time),
        auction_config: {
          trigger_window_minutes: Number(form.trigger_window_minutes),
          extension_duration_minutes: Number(form.extension_duration_minutes),
          trigger_type: form.trigger_type,
        },
      })
      nav(`/rfqs/${data.id}`)
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : (Array.isArray(d) ? d.map((x) => x.msg).join(', ') : 'Failed to create RFQ'))
    } finally { setBusy(false) }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-6 text-2xl font-bold">Create RFQ</h1>
      {error && <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
      <form onSubmit={submit} className="space-y-6">
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 font-semibold">RFQ Information</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div><label className={label}>RFQ Name *</label>
              <input required className={input} value={form.name} onChange={set('name')} /></div>
            <div><label className={label}>Reference ID *</label>
              <input required className={input} value={form.reference_id} onChange={set('reference_id')} placeholder="e.g. RFQ-2026-001" /></div>
            <div className="sm:col-span-2"><label className={label}>Description</label>
              <textarea rows={3} className={input} value={form.description} onChange={set('description')} /></div>
            <div><label className={label}>Pickup Location</label>
              <input className={input} value={form.pickup_location} onChange={set('pickup_location')} /></div>
            <div><label className={label}>Destination Location</label>
              <input className={input} value={form.destination_location} onChange={set('destination_location')} /></div>
            <div><label className={label}>Pickup / Service Date</label>
              <input type="datetime-local" className={input} value={form.service_date} onChange={set('service_date')} /></div>
          </div>
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 font-semibold">Auction Schedule</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div><label className={label}>Bid Start *</label>
              <input required type="datetime-local" className={input} value={form.bid_start_time} onChange={set('bid_start_time')} /></div>
            <div><label className={label}>Bid Close *</label>
              <input required type="datetime-local" className={input} value={form.bid_close_time} onChange={set('bid_close_time')} /></div>
            <div><label className={label}>Forced Close *</label>
              <input required type="datetime-local" className={input} value={form.forced_close_time} onChange={set('forced_close_time')} /></div>
          </div>
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-1 font-semibold">British Auction Rules</h2>
          <p className="mb-4 text-sm text-slate-500">
            Configure when the auction auto-extends. It never extends past the forced close time.
          </p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div><label className={label}>Trigger Window (min) *</label>
              <input required type="number" min="1" className={input} value={form.trigger_window_minutes} onChange={set('trigger_window_minutes')} /></div>
            <div><label className={label}>Extension Duration (min) *</label>
              <input required type="number" min="1" className={input} value={form.extension_duration_minutes} onChange={set('extension_duration_minutes')} /></div>
            <div><label className={label}>Extension Trigger *</label>
              <select className={input} value={form.trigger_type} onChange={set('trigger_type')}>
                <option value="BID_RECEIVED">Any bid in last X min</option>
                <option value="ANY_RANK_CHANGE">Any rank change in last X min</option>
                <option value="L1_RANK_CHANGE">L1 change in last X min</option>
              </select>
            </div>
          </div>
        </section>

        <div className="flex justify-end gap-3">
          <button type="button" onClick={() => nav(-1)}
            className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-medium">Cancel</button>
          <button disabled={busy}
            className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
            {busy ? 'Creating…' : 'Create RFQ'}
          </button>
        </div>
      </form>
    </div>
  )
}
