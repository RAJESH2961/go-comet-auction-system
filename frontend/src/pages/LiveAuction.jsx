import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, TrendingDown, Wifi, WifiOff } from 'lucide-react'
import api from '../services/api'
import { useAuctionSocket } from '../hooks/useAuctionSocket'
import RankingTable from '../components/RankingTable'
import { Countdown, Spinner, StatusBadge, Toast, fmt, fmtDT } from '../components/ui'

export default function LiveAuction() {
  const { id } = useParams()
  const [rfq, setRfq] = useState(null)
  const [auction, setAuction] = useState(null)
  const [rankings, setRankings] = useState([])
  const [myBids, setMyBids] = useState([])
  const [amount, setAmount] = useState('')
  const [error, setError] = useState('')
  const [toast, setToast] = useState(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    const [r, a, rk, mb] = await Promise.all([
      api.get(`/rfqs/${id}`),
      api.get(`/rfqs/${id}/auction`),
      api.get(`/rfqs/${id}/rankings`),
      api.get(`/rfqs/${id}/my-bids`),
    ])
    setRfq(r.data); setAuction(a.data); setRankings(rk.data); setMyBids(mb.data)
  }, [id])

  useEffect(() => { load().catch(() => {}) }, [load])

  const notify = (t) => { setToast(t); setTimeout(() => setToast(null), 4500) }

  const connected = useAuctionSocket(id, (event, data) => {
    if (event === 'new_bid') {
      notify({ type: 'info', message: `New bid ${fmt(data.amount)} — lowest now ${fmt(data.lowest_bid)}` })
      load()
    } else if (event === 'auction_extended') {
      notify({ type: 'info', message: `Extended to ${fmtDT(data.new_close_time)}` })
      load()
    } else if (event === 'auction_status') {
      load()
    }
  })

  if (!rfq || !auction) return <Spinner />
  const live = auction.status === 'ACTIVE'
  const myRank = rankings.find((r) => r.is_me)
  const myLatest = myBids[0]?.amount ?? null
  const baseline = myLatest ?? null

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      await api.post(`/rfqs/${id}/bids`, { amount: parseFloat(amount) })
      setAmount('')
      notify({ type: 'success', message: 'Bid placed' })
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Bid rejected')
    } finally { setBusy(false) }
  }

  return (
    <div>
      <Toast toast={toast} onClose={() => setToast(null)} />
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link to={`/rfqs/${id}`} className="rounded-lg border border-slate-300 p-2 hover:bg-slate-100">
            <ArrowLeft size={18} />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{rfq.name}</h1>
              <StatusBadge status={auction.status} />
              <span title={connected ? 'Live' : 'Reconnecting'}>
                {connected ? <Wifi size={16} className="text-emerald-500" /> : <WifiOff size={16} className="text-red-400" />}
              </span>
            </div>
            <p className="text-sm text-slate-500">{rfq.pickup_location} → {rfq.destination_location}</p>
          </div>
        </div>
        {live && (
          <div className="rounded-xl border-2 border-brand-200 bg-white px-6 py-3 text-center shadow-sm">
            <p className="text-xs font-medium uppercase text-slate-500">Time remaining</p>
            <p className="text-2xl"><Countdown target={auction.current_close_time} onExpire={load} /></p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div className="grid grid-cols-3 gap-4">
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs text-slate-500">Current Lowest (L1)</p>
              <p className="mt-1 text-xl font-bold text-emerald-700">{fmt(auction.lowest_bid)}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs text-slate-500">Your Latest Bid</p>
              <p className="mt-1 text-xl font-bold">{fmt(baseline)}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs text-slate-500">Your Rank</p>
              <p className={`mt-1 text-xl font-bold ${myRank?.rank === 1 ? 'text-emerald-700' : ''}`}>
                {myRank ? myRank.rank_label : '—'}
              </p>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="mb-4 font-semibold">Rankings</h2>
            <RankingTable rankings={rankings} />
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="mb-4 font-semibold">Your Bid History</h2>
            {myBids.length === 0 ? (
              <p className="text-sm text-slate-400">You have not placed any bids yet.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-xs font-semibold uppercase text-slate-500">
                    <th className="py-2 pr-4">Amount</th><th className="py-2">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {myBids.map((b) => (
                    <tr key={b.id} className="border-b border-slate-50">
                      <td className="py-2.5 pr-4 font-semibold">{fmt(b.amount)}</td>
                      <td className="py-2.5 text-slate-500">{fmtDT(b.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm h-fit">
          <div className="mb-4 flex items-center gap-2">
            <TrendingDown className="text-brand-600" size={20} />
            <h2 className="font-semibold">Place a Lower Bid</h2>
          </div>
          {!live ? (
            <p className="rounded-lg bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">
              {auction.status === 'UPCOMING'
                ? `Auction starts ${fmtDT(auction.bid_start_time)}`
                : 'This auction has ended.'}
            </p>
          ) : (
            <form onSubmit={submit} className="space-y-4">
              {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
              <div>
                <label className="mb-1 block text-sm font-medium">Bid amount (₹)</label>
                <input required type="number" min="1" step="0.01" value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder={baseline ? `Below ${baseline}` : 'Enter amount'}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-lg font-semibold focus:border-brand-500 focus:outline-none" />
                {baseline && (
                  <p className="mt-1 text-xs text-slate-500">
                    Must be lower than your current bid of {fmt(baseline)}.
                  </p>
                )}
              </div>
              <button disabled={busy}
                className="w-full rounded-lg bg-emerald-600 py-3 text-sm font-bold text-white hover:bg-emerald-700 disabled:opacity-60">
                {busy ? 'Placing…' : 'Submit Bid'}
              </button>
              <p className="text-xs text-slate-400">
                Bids are final. Each new bid must beat your own previous bid.
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
