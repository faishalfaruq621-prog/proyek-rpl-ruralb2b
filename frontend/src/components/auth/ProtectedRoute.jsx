import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { getCapabilities } from '../../utils/capabilities'

export function ProtectedRoute({ children, roles = [], capability }) {
  const { user, loading, isAuthenticated } = useAuth()

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rural-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: window.location.pathname }} />
  }

  if (roles.length && !roles.includes(user.role)) {
    return <Navigate to="/" replace />
  }

  // Proteksi berbasis kemampuan (Buyer / Seller), bukan sekadar sembunyikan
  // menu. Akses langsung via URL tetap ditolak bila tidak berhak.
  if (capability && !getCapabilities(user)[capability]) {
    return <Navigate to="/" replace />
  }

  return children || <Outlet />
}

export default ProtectedRoute
