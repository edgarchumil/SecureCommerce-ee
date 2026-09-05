import { useQuery } from '@tanstack/react-query'
import { Navigate, Outlet } from 'react-router-dom'
import { getProfile } from '../../api/auth'
import { useAuth } from './AuthContext'

export function AdminRoute() {
  const { token } = useAuth()
  const profile = useQuery({ queryKey: ['profile', token], queryFn: getProfile })
  if (profile.isPending) return <p className="p-8">Verificando permisos...</p>
  if (!['org_admin', 'superadmin'].includes(profile.data?.role_code ?? '')) return <Navigate replace to="/panel" />
  return <Outlet />
}
