import { useAuth } from '../context/AuthContext'

export function useAuthGuard() {
  const { user, loading, login, logout, isAuthenticated } = useAuth()
  return { user, loading, login, logout, isAuthenticated }
}
