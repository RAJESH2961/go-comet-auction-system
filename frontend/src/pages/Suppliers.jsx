import { useEffect, useState } from 'react'
import api from '../services/api'
import { EmptyState, Spinner, fmtDT } from '../components/ui'

export default function Suppliers() {
  const [suppliers, setSuppliers] = useState(null)

  useEffect(() => {
    api.get('/suppliers').then((r) => setSuppliers(r.data))
  }, [])

  if (!suppliers) return <Spinner />

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Registered Suppliers</h1>
      {suppliers.length === 0 ? (
        <EmptyState title="No suppliers registered yet" />
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/60 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <th className="px-5 py-3">Supplier</th>
                <th className="px-5 py-3">Company</th>
                <th className="px-5 py-3">Email</th>
                <th className="px-5 py-3">Phone</th>
                <th className="px-5 py-3">Quotes</th>
                <th className="px-5 py-3">Bids</th>
                <th className="px-5 py-3">Joined</th>
              </tr>
            </thead>
            <tbody>
              {suppliers.map((s) => (
                <tr key={s.id} className="border-b border-slate-50">
                  <td className="px-5 py-3 font-medium">{s.full_name}</td>
                  <td className="px-5 py-3">{s.company_name || '—'}</td>
                  <td className="px-5 py-3 text-slate-600">{s.email}</td>
                  <td className="px-5 py-3 text-slate-600">{s.phone || '—'}</td>
                  <td className="px-5 py-3">{s.quotes_count}</td>
                  <td className="px-5 py-3">{s.bids_count}</td>
                  <td className="px-5 py-3 text-slate-500">{fmtDT(s.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
