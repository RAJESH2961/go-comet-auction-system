import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  FileText, Gavel, LayoutDashboard, LogOut, Plus, Users, UserCircle,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const linkCls = ({ isActive }) =>
  `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
    isActive ? 'bg-brand-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
  }`

export default function DashboardLayout() {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const isBuyer = user?.role === 'BUYER'

  return (
    <div className="flex min-h-screen">
      <aside className="fixed inset-y-0 left-0 flex w-60 flex-col bg-slate-900 px-4 py-6">
        <div className="mb-8 px-2">
          <h1 className="text-lg font-bold text-white">RFQ Auctions</h1>
          <p className="text-xs text-slate-400">{isBuyer ? 'Buyer Portal' : 'Supplier Portal'}</p>
        </div>
        <nav className="flex-1 space-y-1">
          <NavLink to="/dashboard" className={linkCls}>
            <LayoutDashboard size={17} /> Dashboard
          </NavLink>
          <NavLink to="/rfqs" className={linkCls}>
            <FileText size={17} /> {isBuyer ? 'My RFQs' : 'Available RFQs'}
          </NavLink>
          {isBuyer && (
            <>
              <NavLink to="/rfqs/new" className={linkCls}>
                <Plus size={17} /> Create RFQ
              </NavLink>
              <NavLink to="/suppliers" className={linkCls}>
                <Users size={17} /> Suppliers
              </NavLink>
            </>
          )}
          <NavLink to="/profile" className={linkCls}>
            <UserCircle size={17} /> Profile
          </NavLink>
        </nav>
        <div className="border-t border-slate-700 pt-4">
          <div className="px-2 pb-3">
            <p className="truncate text-sm font-medium text-white">{user?.full_name}</p>
            <p className="truncate text-xs text-slate-400">{user?.email}</p>
          </div>
          <button
            onClick={() => { logout(); nav('/login') }}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white"
          >
            <LogOut size={17} /> Logout
          </button>
        </div>
      </aside>
      <main className="ml-60 flex-1 p-8">
        <Outlet />
      </main>
    </div>
  )
}
