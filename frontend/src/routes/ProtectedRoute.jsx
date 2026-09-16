import { Navigate, useLocation } from 'react-router-dom'
import { auth } from '../services/auth'

export function ProtectedRoute({ children, allowedRoles = [], redirectTo = '/login' }) {
  const location = useLocation()
  const user = auth.getUser()

  if (!auth.isAuthenticated() || !user) {
    return <Navigate to={redirectTo} replace state={{ from: location.pathname }} />
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    const roleRedirect =
      user.role === 'applicant'
        ? '/applicant/dashboard'
        : user.role === 'recruiter'
          ? '/hiring/dashboard'
          : user.role === 'government'
            ? '/government/dashboard'
            : '/'

    return <Navigate to={roleRedirect} replace />
  }

  return children
}
