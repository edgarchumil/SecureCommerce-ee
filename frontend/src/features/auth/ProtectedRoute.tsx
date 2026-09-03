import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from './AuthContext'

export function ProtectedRoute() {
  const { token, initializing } = useAuth()
  const location = useLocation()
  if (initializing) return <p className="p-8 text-slate-700">Verificando sesión…</p>
  if (!token) return <Navigate replace state={{ from: location }} to="/login" />
  return <Outlet />
}

