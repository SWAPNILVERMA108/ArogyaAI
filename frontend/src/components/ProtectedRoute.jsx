import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { HOME_BY_ROLE } from '../constants'
import { useAuth } from '../context/AuthContext'
import { Spinner } from './ui'

// Requires a signed-in user; optionally restricts to specific roles.
export default function ProtectedRoute({ roles }) {
  const { user, initialising } = useAuth()
  const location = useLocation()

  if (initialising) return <Spinner />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (roles && !roles.includes(user.role)) return <Navigate to={HOME_BY_ROLE[user.role] || '/'} replace />
  return <Outlet />
}
