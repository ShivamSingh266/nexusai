import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'
import { getRoleHome } from './roleUtils'

export function ProtectedRoute({ allowedRoles }) {
  const { currentUser, loading } = useAuth()
  const location = useLocation()

  if (loading) return <div className="p-8 text-sm text-slate-600">Loading your session...</div>
  if (!currentUser) return <Navigate to="/login" replace state={{ from: location }} />
  if (allowedRoles && !allowedRoles.includes(currentUser.role)) {
    return <Navigate to={getRoleHome(currentUser.role)} replace />
  }
  return <Outlet />
}
