import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './routes/ProtectedRoute'
import DashboardLayout from './layouts/DashboardLayout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import RFQList from './pages/RFQList'
import CreateRFQ from './pages/CreateRFQ'
import RFQDetails from './pages/RFQDetails'
import LiveAuction from './pages/LiveAuction'
import Suppliers from './pages/Suppliers'
import Profile from './pages/Profile'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/rfqs" element={<RFQList />} />
            <Route path="/rfqs/new" element={<ProtectedRoute role="BUYER"><CreateRFQ /></ProtectedRoute>} />
            <Route path="/rfqs/:id" element={<RFQDetails />} />
            <Route path="/rfqs/:id/live" element={<ProtectedRoute role="SUPPLIER"><LiveAuction /></ProtectedRoute>} />
            <Route path="/suppliers" element={<ProtectedRoute role="BUYER"><Suppliers /></ProtectedRoute>} />
            <Route path="/profile" element={<Profile />} />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
