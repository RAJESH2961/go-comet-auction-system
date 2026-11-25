import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Search } from 'lucide-react'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { EmptyState, Spinner, StatusBadge, fmt, fmtDT } from '../components/ui'

const STATUSES = ['', 'UPCOMING', 'ACTIVE', 'CLOSED', 'FORCE_CLOSED']

export default function RFQList() {
  const { user } = useAuth()
  const isBuyer = user?.role === 'BUYER'
  const [data, setData] = useState(null)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)

  useEffect(() => {
    const t = setTimeout(() => {
      api.get('/rfqs', { params: { search: search || undefined, status: status || undefined, page, page_size: 10 } })
        .then((r) => setData(r.data))
    }, 250)
    return () => clearTimeout(t)
  }, [search, status, page])

  const pages = data ? Math.max(1, Math.ceil(data.total / 10)) : 1

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">{isBuyer ? 'My RFQs' : 'Available RFQs'}</h1>
        {isBuyer && (
          <Link to="/rfqs/new" className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700">
            + Create RFQ
          </Link>
        )}
      </div>

      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative">
          <Search size={16} className="absolute left-3 top-2.5 text-slate-400" />
          <input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            placeholder="Search name or reference…"
            className="w-72 rounded-lg border border-slate-300 py-2 pl-9 pr-3 text-sm focus:border-brand-500 focus:outline-none" />
        </div>
        <div className="flex gap-1 rounded-lg border border-slate-200 bg-white p-1">
          {STATUSES.map((s) => (
            <button key={s || 'all'} onClick={() => { setStatus(s); setPage(1) }}
              className={`rounded-md px-3 py-1 text-xs font-medium ${status === s ? 'bg-brand-600 text-white' : 'text-slate-500 hover:bg-slate-100'}`}>
              {s ? s.replace('_', ' ') : 'All'}
            </button>
          ))}
        </div>
      </div>

      {!data ? <Spinner /> : data.items.length === 0 ? (
        <EmptyState title="No RFQs found" hint="Try adjusting your search or filters." />
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/60 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <th className="px-5 py-3">RFQ</th>
                <th className="px-5 py-3">Route</th>
                <th className="px-5 py-3">Starts</th>
                <th className="px-5 py-3">Current Close</th>
                <th className="px-5 py-3">Forced Close</th>
                <th className="px-5 py-3">Lowest Bid</th>
                <th className="px-5 py-3">Suppliers</th>
                <th className="px-5 py-3">Bids</th>
                <th className="px-5 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((r) => (
                <tr key={r.id} className="border-b border-slate-50 hover:bg-slate-50/60">
                  <td className="px-5 py-3">
                    <Link to={`/rfqs/${r.id}`} className="font-medium text-brand-600 hover:underline">{r.name}</Link>
                    <div className="text-xs text-slate-400">{r.reference_id}</div>
                  </td>
                  <td className="px-5 py-3 text-slate-600">{r.pickup_location} → {r.destination_location}</td>
                  <td className="px-5 py-3 text-slate-600">{fmtDT(r.bid_start_time)}</td>
                  <td className="px-5 py-3 text-slate-600">{fmtDT(r.current_close_time)}</td>
                  <td className="px-5 py-3 text-slate-600">{fmtDT(r.forced_close_time)}</td>
                  <td className="px-5 py-3 font-semibold">{fmt(r.lowest_bid)}</td>
                  <td className="px-5 py-3">{r.supplier_count}</td>
                  <td className="px-5 py-3">{r.bid_count}</td>
                  <td className="px-5 py-3"><StatusBadge status={r.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3 text-sm">
            <span className="text-slate-500">{data.total} result{data.total !== 1 ? 's' : ''}</span>
            <div className="flex gap-2">
              <button disabled={page <= 1} onClick={() => setPage(page - 1)}
                className="rounded-md border border-slate-300 px-3 py-1 disabled:opacity-40">Prev</button>
              <span className="py-1 text-slate-500">Page {page} / {pages}</span>
              <button disabled={page >= pages} onClick={() => setPage(page + 1)}
                className="rounded-md border border-slate-300 px-3 py-1 disabled:opacity-40">Next</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
