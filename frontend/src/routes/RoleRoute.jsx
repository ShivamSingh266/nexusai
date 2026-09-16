import { Navigate } from 'react-router-dom'
import { auth, getDefaultDashboardForRole } from '../services/auth'

export function RoleRoute({ allowedRoles = [], children, fallbackPath = '/login' }) {
  const user = auth.getUser()

  if (!auth.isAuthenticated() || !user) {
    return <Navigate to={fallbackPath} replace />
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return <Navigate to={getDefaultDashboardForRole(user.role)} replace />
  }

  return children
}
