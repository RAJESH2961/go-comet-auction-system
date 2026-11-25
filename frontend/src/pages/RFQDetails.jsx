import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Gavel } from 'lucide-react'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useAuctionSocket } from '../hooks/useAuctionSocket'
import RankingTable from '../components/RankingTable'
import {
  Countdown, EmptyState, Modal, Spinner, StatusBadge, Toast, fmt, fmtDT,
} from '../components/ui'

const input = 'w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none'
const label = 'mb-1 block text-sm font-medium text-slate-700'

function QuoteModal({ rfqId, onClose, onDone }) {
  const [f, setF] = useState({
    carrier_name: '', freight_charges: '', origin_charges: '',
    destination_charges: '', transit_time: '', validity_of_quote: '',
  })
  const [error, setError] = useState('')
  const total = ['freight_charges', 'origin_charges', 'destination_charges']
    .reduce((s, k) => s + (parseFloat(f[k]) || 0), 0)

  const submit = async (e) => {
    e.preventDefault()
    try {
      await api.post(`/rfqs/${rfqId}/quotes`, {
        carrier_name: f.carrier_name,
        freight_charges: parseFloat(f.freight_charges) || 0,
        origin_charges: parseFloat(f.origin_charges) || 0,
        destination_charges: parseFloat(f.destination_charges) || 0,
        transit_time: f.transit_time || null,
        validity_of_quote: f.validity_of_quote ? new Date(f.validity_of_quote).toISOString() : null,
      })
      onDone()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit quote')
    }
  }

  const num = (k, l) => (
    <div><label className={label}>{l} *</label>
      <input required type="number" min="0" step="0.01" className={input}
        value={f[k]} onChange={(e) => setF({ ...f, [k]: e.target.value })} /></div>
  )

  return (
    <Modal open title="Submit Initial Quotation" onClose={onClose}>
      {error && <div className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
      <form onSubmit={submit} className="grid grid-cols-2 gap-3">
        <div className="col-span-2"><label className={label}>Carrier Name *</label>
          <input required className={input} value={f.carrier_name}
            onChange={(e) => setF({ ...f, carrier_name: e.target.value })} /></div>
        {num('freight_charges', 'Freight Charges')}
        {num('origin_charges', 'Origin Charges')}
        {num('destination_charges', 'Destination Charges')}
        <div><label className={label}>Transit Time</label>
          <input className={input} placeholder="e.g. 3 days" value={f.transit_time}
            onChange={(e) => setF({ ...f, transit_time: e.target.value })} /></div>
        <div className="col-span-2"><label className={label}>Quote Valid Until</label>
          <input type="datetime-local" className={input} value={f.validity_of_quote}
            onChange={(e) => setF({ ...f, validity_of_quote: e.target.value })} /></div>
        <div className="col-span-2 rounded-lg bg-slate-50 px-4 py-3 text-sm">
          Total bid: <span className="text-lg font-bold text-brand-700">{fmt(total)}</span>
        </div>
        <button className="col-span-2 rounded-lg bg-brand-600 py-2.5 text-sm font-semibold text-white hover:bg-brand-700">
          Submit Quotation
        </button>
      </form>
    </Modal>
  )
}

const EVENT_LABELS = {
  RFQ_CREATED: 'RFQ created', RFQ_UPDATED: 'RFQ updated',
  SUPPLIER_JOINED: 'Supplier joined', QUOTE_SUBMITTED: 'Quote submitted',
  BID_RECEIVED: 'Bid received', RANK_CHANGED: 'Ranking changed',
  AUCTION_EXTENDED: 'Auction extended', AUCTION_STARTED: 'Auction started',
  AUCTION_CLOSED: 'Auction closed', AUCTION_FORCE_CLOSED: 'Forced close',
}

export default function RFQDetails() {
  const { id } = useParams()
  const { user } = useAuth()
  const isBuyer = user?.role === 'BUYER'
  const [rfq, setRfq] = useState(null)
  const [auction, setAuction] = useState(null)
  const [rankings, setRankings] = useState([])
  const [bids, setBids] = useState([])
  const [activity, setActivity] = useState([])
  const [quotes, setQuotes] = useState([])
  const [tab, setTab] = useState('overview')
  const [showQuote, setShowQuote] = useState(false)
  const [toast, setToast] = useState(null)

  const load = useCallback(async () => {
    const [r, a, rk, b, act, q] = await Promise.all([
      api.get(`/rfqs/${id}`),
      api.get(`/rfqs/${id}/auction`),
      api.get(`/rfqs/${id}/rankings`),
      api.get(`/rfqs/${id}/bids`),
      api.get(`/rfqs/${id}/activity`),
      api.get(`/rfqs/${id}/quotes`),
    ])
    setRfq(r.data); setAuction(a.data); setRankings(rk.data)
    setBids(b.data); setActivity(act.data); setQuotes(q.data)
  }, [id])

  useEffect(() => { load().catch(() => {}) }, [load])

  const notify = (t) => { setToast(t); setTimeout(() => setToast(null), 4000) }

  useAuctionSocket(id, (event, data) => {
    if (event === 'new_bid') {
      notify({ type: 'info', message: `New bid: ${fmt(data.amount)} by ${data.supplier_name}` })
      load()
    } else if (event === 'auction_extended') {
      notify({ type: 'info', message: `Auction extended to ${fmtDT(data.new_close_time)}` })
      load()
    } else if (event === 'auction_status') {
      load()
    }
  })

  if (!rfq || !auction) return <Spinner />
  const live = auction.status === 'ACTIVE'
  const myQuote = quotes[0]

  return (
    <div>
      <Toast toast={toast} onClose={() => setToast(null)} />
      {showQuote && (
        <QuoteModal rfqId={id} onClose={() => setShowQuote(false)}
          onDone={() => { setShowQuote(false); notify({ type: 'success', message: 'Quotation submitted' }); load() }} />
      )}

      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{rfq.name}</h1>
            <StatusBadge status={auction.status} />
          </div>
          <p className="mt-1 text-sm text-slate-500">
            {rfq.reference_id} · {rfq.pickup_location} → {rfq.destination_location}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {live && (
            <div className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm shadow-sm">
              Closes in <Countdown target={auction.current_close_time} onExpire={load} />
            </div>
          )}
          {!isBuyer && !myQuote && auction.status !== 'CLOSED' && auction.status !== 'FORCE_CLOSED' && (
            <button onClick={() => setShowQuote(true)}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700">
              Submit Quotation
            </button>
          )}
          {!isBuyer && myQuote && live && (
            <Link to={`/rfqs/${id}/live`}
              className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700">
              <Gavel size={16} /> Enter Live Auction
            </Link>
          )}
        </div>
      </div>

      <div className="mb-5 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs text-slate-500">Current Lowest</p>
          <p className="mt-1 text-xl font-bold text-emerald-700">{fmt(auction.lowest_bid)}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs text-slate-500">Suppliers</p>
          <p className="mt-1 text-xl font-bold">{auction.supplier_count}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs text-slate-500">Total Bids</p>
          <p className="mt-1 text-xl font-bold">{auction.total_bids}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs text-slate-500">Closes At</p>
          <p className="mt-1 text-sm font-semibold">{fmtDT(auction.current_close_time)}</p>
          <p className="text-xs text-slate-400">Hard stop {fmtDT(auction.forced_close_time)}</p>
        </div>
      </div>

      <div className="mb-4 flex gap-1 rounded-lg border border-slate-200 bg-white p-1">
        {['overview', 'rankings', 'bids', 'quotes', 'activity'].map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`rounded-md px-4 py-1.5 text-sm font-medium capitalize ${tab === t ? 'bg-brand-600 text-white' : 'text-slate-500 hover:bg-slate-100'}`}>
            {t === 'quotes' ? (isBuyer ? 'Quotations' : 'My Quote') : t === 'bids' ? 'Bid History' : t}
          </button>
        ))}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        {tab === 'overview' && (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <dl className="space-y-3 text-sm">
              {[
                ['Description', rfq.description],
                ['Service Date', fmtDT(rfq.service_date)],
                ['Bid Start', fmtDT(rfq.bid_start_time)],
                ['Initial Close', fmtDT(rfq.bid_close_time)],
                ['Current Close', fmtDT(auction.current_close_time)],
                ['Forced Close', fmtDT(auction.forced_close_time)],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between border-b border-slate-50 pb-2">
                  <dt className="text-slate-500">{k}</dt><dd className="font-medium">{v || '—'}</dd>
                </div>
              ))}
            </dl>
            <dl className="space-y-3 text-sm">
              {[
                ['Trigger Type', rfq.auction_config?.trigger_type?.replace(/_/g, ' ')],
                ['Trigger Window', `${rfq.auction_config?.trigger_window_minutes} min`],
                ['Extension Duration', `${rfq.auction_config?.extension_duration_minutes} min`],
                ['L1 Supplier', rankings[0] ? rankings[0].company_name || rankings[0].supplier_name : '—'],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between border-b border-slate-50 pb-2">
                  <dt className="text-slate-500">{k}</dt><dd className="font-medium">{v || '—'}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}

        {tab === 'rankings' && <RankingTable rankings={rankings} />}

        {tab === 'bids' && (
          bids.length === 0 ? <EmptyState title="No bids yet" /> : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs font-semibold uppercase text-slate-500">
                  <th className="py-2 pr-4">Supplier</th>
                  <th className="py-2 pr-4">Previous</th>
                  <th className="py-2 pr-4">New Bid</th>
                  <th className="py-2">Time</th>
                </tr>
              </thead>
              <tbody>
                {[...bids].reverse().map((b) => (
                  <tr key={b.id} className="border-b border-slate-50">
                    <td className="py-2.5 pr-4">{b.supplier_name}</td>
                    <td className="py-2.5 pr-4 text-slate-500">{fmt(b.previous_amount)}</td>
                    <td className="py-2.5 pr-4 font-semibold text-emerald-700">{fmt(b.amount)}</td>
                    <td className="py-2.5 text-slate-500">{fmtDT(b.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        )}

        {tab === 'quotes' && (
          quotes.length === 0 ? <EmptyState title="No quotations yet" /> : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs font-semibold uppercase text-slate-500">
                  <th className="py-2 pr-4">Supplier</th><th className="py-2 pr-4">Carrier</th>
                  <th className="py-2 pr-4">Freight</th><th className="py-2 pr-4">Origin</th>
                  <th className="py-2 pr-4">Destination</th><th className="py-2 pr-4">Total</th>
                  <th className="py-2">Transit</th>
                </tr>
              </thead>
              <tbody>
                {quotes.map((q) => (
                  <tr key={q.id} className="border-b border-slate-50">
                    <td className="py-2.5 pr-4">{q.supplier_name || 'You'}</td>
                    <td className="py-2.5 pr-4">{q.carrier_name}</td>
                    <td className="py-2.5 pr-4">{fmt(q.freight_charges)}</td>
                    <td className="py-2.5 pr-4">{fmt(q.origin_charges)}</td>
                    <td className="py-2.5 pr-4">{fmt(q.destination_charges)}</td>
                    <td className="py-2.5 pr-4 font-semibold">{fmt(q.total_amount)}</td>
                    <td className="py-2.5 text-slate-500">{q.transit_time || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        )}

        {tab === 'activity' && (
          activity.length === 0 ? <EmptyState title="No activity yet" /> : (
            <ol className="relative space-y-4 border-l border-slate-200 pl-5">
              {activity.map((a) => (
                <li key={a.id}>
                  <span className="absolute -left-1.5 mt-1.5 h-3 w-3 rounded-full border-2 border-white bg-brand-400" />
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    {EVENT_LABELS[a.event_type] || a.event_type}
                  </p>
                  <p className="text-sm">{a.message}</p>
                  <p className="text-xs text-slate-400">{fmtDT(a.created_at)}</p>
                </li>
              ))}
            </ol>
          )
        )}
      </div>
    </div>
  )
}
