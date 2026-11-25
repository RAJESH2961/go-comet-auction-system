import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Activity, Clock, FileText, Gavel, TrendingDown, Users,
} from 'lucide-react'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { EmptyState, Spinner, StatCard, StatusBadge, fmt, fmtDT } from '../components/ui'

export default function Dashboard() {
  const { user } = useAuth()
  const isBuyer = user?.role === 'BUYER'
  const [stats, setStats] = useState(null)
  const [rfqs, setRfqs] = useState([])

  useEffect(() => {
    api.get('/dashboard/stats').then((r) => setStats(r.data))
    api.get('/rfqs', { params: { page_size: 5 } }).then((r) => setRfqs(r.data.items))
  }, [])

  if (!stats) return <Spinner />

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Welcome back, {user.full_name.split(' ')[0]}</h1>
          <p className="text-sm text-slate-500">
            {isBuyer ? 'Monitor your RFQs and live auctions.' : 'Find RFQs and compete in live auctions.'}
          </p>
        </div>
        {isBuyer && (
          <Link to="/rfqs/new"
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700">
            + Create RFQ
          </Link>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <StatCard icon={FileText} label={isBuyer ? 'Total RFQs' : 'RFQs Available'} value={stats.total_rfqs} />
        <StatCard icon={Gavel} label="Active Auctions" value={stats.active_auctions}
          accent="text-emerald-600 bg-emerald-50" />
        <StatCard icon={Clock} label="Upcoming" value={stats.upcoming_auctions}
          accent="text-blue-600 bg-blue-50" />
        <StatCard icon={Activity} label="Closed" value={stats.closed_auctions}
          accent="text-slate-600 bg-slate-100" />
        <StatCard icon={Users} label={isBuyer ? 'Registered Suppliers' : 'My Quotations'}
          value={stats.total_suppliers} accent="text-violet-600 bg-violet-50" />
        <StatCard icon={TrendingDown} label={isBuyer ? 'Bids Received' : 'My Bids'}
          value={stats.total_bids} accent="text-amber-600 bg-amber-50" />
      </div>

      <div className="mt-8 rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <h2 className="font-semibold">Recent RFQs</h2>
          <Link to="/rfqs" className="text-sm font-medium text-brand-600 hover:underline">View all</Link>
        </div>
        {rfqs.length === 0 ? (
          <EmptyState title="No RFQs yet"
            hint={isBuyer ? 'Create your first RFQ to start an auction.' : 'Check back soon for new opportunities.'} />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <th className="px-5 py-3">RFQ</th>
                <th className="px-5 py-3">Route</th>
                <th className="px-5 py-3">Closes</th>
                <th className="px-5 py-3">Lowest Bid</th>
                <th className="px-5 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {rfqs.map((r) => (
                <tr key={r.id} className="border-b border-slate-50 hover:bg-slate-50/60">
                  <td className="px-5 py-3">
                    <Link to={`/rfqs/${r.id}`} className="font-medium text-brand-600 hover:underline">
                      {r.name}
                    </Link>
                    <div className="text-xs text-slate-400">{r.reference_id}</div>
                  </td>
                  <td className="px-5 py-3 text-slate-600">
                    {r.pickup_location} → {r.destination_location}
                  </td>
                  <td className="px-5 py-3 text-slate-600">{fmtDT(r.current_close_time)}</td>
                  <td className="px-5 py-3 font-semibold">{fmt(r.lowest_bid)}</td>
                  <td className="px-5 py-3"><StatusBadge status={r.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
