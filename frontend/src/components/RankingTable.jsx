import { Crown } from 'lucide-react'
import { fmt } from './ui'

export default function RankingTable({ rankings }) {
  if (!rankings?.length)
    return <p className="py-6 text-center text-sm text-slate-400">No participants yet.</p>
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-slate-200 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <th className="py-2 pr-4">Rank</th>
          <th className="py-2 pr-4">Supplier</th>
          <th className="py-2 pr-4">Latest Bid</th>
          <th className="py-2">Transit Time</th>
        </tr>
      </thead>
      <tbody>
        {rankings.map((r) => (
          <tr key={r.supplier_id}
            className={`border-b border-slate-100 ${r.rank === 1 ? 'bg-emerald-50/60' : ''} ${r.is_me ? 'outline outline-1 outline-brand-200 bg-brand-50/50' : ''}`}>
            <td className="py-2.5 pr-4">
              <span className={`inline-flex items-center gap-1 font-semibold ${r.rank === 1 ? 'text-emerald-700' : 'text-slate-600'}`}>
                {r.rank === 1 && <Crown size={14} />} {r.rank_label}
              </span>
            </td>
            <td className="py-2.5 pr-4">
              {r.is_me ? 'You' : (r.company_name || r.supplier_name)}
            </td>
            <td className="py-2.5 pr-4 font-semibold">{fmt(r.latest_bid)}</td>
            <td className="py-2.5 text-slate-500">{r.transit_time || '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
