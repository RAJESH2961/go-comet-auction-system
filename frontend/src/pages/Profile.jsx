import { useState } from 'react'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

const input = 'w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none'
const label = 'mb-1 block text-sm font-medium text-slate-700'

export default function Profile() {
  const { user, setUser } = useAuth()
  const [form, setForm] = useState({
    full_name: user?.full_name || '',
    company_name: user?.company_name || '',
    phone: user?.phone || '',
  })
  const [msg, setMsg] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    const { data } = await api.put('/auth/profile', form)
    setUser(data)
    setMsg('Profile updated')
    setTimeout(() => setMsg(''), 3000)
  }

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="mb-6 text-2xl font-bold">Profile</h1>
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-5 flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-brand-100 text-xl font-bold text-brand-700">
            {user?.full_name?.[0]?.toUpperCase()}
          </div>
          <div>
            <p className="font-semibold">{user?.full_name}</p>
            <p className="text-sm text-slate-500">{user?.email} · {user?.role}</p>
          </div>
        </div>
        {msg && <div className="mb-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{msg}</div>}
        <form onSubmit={submit} className="space-y-4">
          <div><label className={label}>Full name</label>
            <input className={input} value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></div>
          <div><label className={label}>Company name</label>
            <input className={input} value={form.company_name}
              onChange={(e) => setForm({ ...form, company_name: e.target.value })} /></div>
          <div><label className={label}>Phone</label>
            <input className={input} value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
          <button className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700">
            Save changes
          </button>
        </form>
      </div>
    </div>
  )
}
