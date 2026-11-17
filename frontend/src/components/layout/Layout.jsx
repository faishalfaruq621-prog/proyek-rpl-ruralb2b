import { Outlet, useLocation } from 'react-router-dom'
import { Navbar } from './Navbar'
import { Footer } from './Footer'
import { FloatingAIChat } from '../ai/FloatingAIChat'
import { useAuth } from '../../context/AuthContext'

export function Layout() {
  const { user, logout } = useAuth()
  const location = useLocation()

  const authRoutes = ['/login', '/register']

  return (
    <div className="min-h-screen flex flex-col bg-earth-50">
      {!authRoutes.includes(location.pathname) && <Navbar user={user} onLogout={logout} />}
      <main className="flex-grow pt-20 pb-8">
        <Outlet />
      </main>
      {!authRoutes.includes(location.pathname) && <Footer />}
      {user && !authRoutes.includes(location.pathname) && <FloatingAIChat />}
    </div>
  )
}

export default Layout
