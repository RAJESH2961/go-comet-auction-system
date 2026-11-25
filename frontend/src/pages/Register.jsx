import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Gavel } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const { register } = useAuth()
  const nav = useNavigate()
  const [form, setForm] = useState({
    full_name: '', email: '', password: '', role: 'SUPPLIER',
    company_name: '', phone: '',
  })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      await register(form)
      nav('/dashboard')
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : 'Registration failed')
    } finally { setBusy(false) }
  }

  const field = (key, label, type = 'text', required = true) => (
    <div>
      <label className="mb-1 block text-sm font-medium">{label}</label>
      <input type={type} required={required} value={form[key]}
        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100" />
    </div>
  )

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-brand-950 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl">
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-xl bg-brand-600 p-2.5 text-white"><Gavel size={22} /></div>
          <div>
            <h1 className="text-xl font-bold">Create Account</h1>
            <p className="text-sm text-slate-500">Join the auction platform</p>
          </div>
        </div>
        {error && <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <form onSubmit={submit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            {['BUYER', 'SUPPLIER'].map((r) => (
              <button type="button" key={r}
                onClick={() => setForm({ ...form, role: r })}
                className={`rounded-lg border px-3 py-2.5 text-sm font-semibold transition ${
                  form.role === r
                    ? 'border-brand-600 bg-brand-50 text-brand-700'
                    : 'border-slate-300 text-slate-500 hover:border-slate-400'
                }`}>
                {r === 'BUYER' ? 'I am a Buyer' : 'I am a Supplier'}
              </button>
            ))}
          </div>
          {field('full_name', 'Full name')}
          {field('email', 'Email', 'email')}
          {field('password', 'Password (min 8 chars)', 'password')}
          {field('company_name', 'Company name', 'text', false)}
          {field('phone', 'Phone', 'text', false)}
          <button disabled={busy}
            className="w-full rounded-lg bg-brand-600 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
            {busy ? 'Creating…' : 'Create account'}
          </button>
        </form>
        <p className="mt-5 text-center text-sm text-slate-500">
          Have an account? <Link to="/login" className="font-medium text-brand-600 hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
