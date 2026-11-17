import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authService } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadUser = useCallback(async () => {
    try {
      const res = await authService.me()
      setUser(res.data.data.user || res.data.data)
    } catch (err) {
      setUser(null)
      // Token tidak valid / kedaluwarsa / dicabut (401 pada /auth/me):
      // bersihkan token agar pengguna tidak terjebak dalam sesi mati.
      localStorage.removeItem('ruralb2b_token')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (localStorage.getItem('ruralb2b_token')) {
      loadUser()
    } else {
      setLoading(false)
    }
  }, [loadUser])

  const login = async (credentials) => {
    const res = await authService.login(credentials)
    const token = res.data.data.access_token
    localStorage.setItem('ruralb2b_token', token)
    setUser(res.data.data.user || res.data.data)
    return res
  }

  const register = async (data) => {
    const res = await authService.register(data)
    return res
  }

  const logout = async () => {
    try {
      await authService.logout()
    } catch (err) {
      // ignore logout errors
    }
    localStorage.removeItem('ruralb2b_token')
    setUser(null)
    window.location.href = '/login'
  }

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export default AuthContext
