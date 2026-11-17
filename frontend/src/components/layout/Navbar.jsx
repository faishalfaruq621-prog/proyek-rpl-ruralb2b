import { useState, useEffect, useRef } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, X, Search, ChevronDown, MessageSquare, Bell } from 'lucide-react'
import { getCapabilities } from '../../utils/capabilities'
import { notificationService } from '../../api/auth'

const buyerMenu = [
  { to: '/keranjang', label: 'Keranjang' },
  { to: '/pesanan', label: 'Pesanan Saya' },
  { to: '/pesanan?status=completed', label: 'Riwayat Transaksi' },
  { to: '/ai/recommendations', label: 'AI Product Recommendation' },
]

const sellerMenu = [
  { to: '/dashboard', label: 'Dashboard Penjual' },
  { to: '/produk/kelola', label: 'Produk Saya' },
  { to: '/produk/tambah', label: 'Tambah Produk' },
  { to: '/seller/pesanan?status=pending', label: 'Pesanan Masuk' },
  { to: '/seller/pesanan', label: 'Riwayat Penjualan' },
  { to: '/ai/insights', label: 'AI Business Insights' },
]

export function Navbar({ user, onLogout }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [openDropdown, setOpenDropdown] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [unreadCount, setUnreadCount] = useState(0)
  const location = useLocation()
  const dropdownRef = useRef(null)

  const caps = getCapabilities(user)

  // Badge notifikasi: polling ringan 60 detik hanya saat user login.
  useEffect(() => {
    if (!user) {
      setUnreadCount(0)
      return
    }
    let mounted = true
    const load = async () => {
      try {
        const res = await notificationService.getUnreadCount()
        const count = res.data?.data?.unread_count
        if (mounted) setUnreadCount(Number(count) || 0)
      } catch {
        // Hening: badge tidak boleh mengganggu navigasi.
      }
    }
    load()
    const interval = setInterval(() => {
      if (!document.hidden) load()
    }, 60000)
    // Badge diperbarui segera saat halaman lain menandai notifikasi dibaca.
    window.addEventListener('ruralb2b:notif-changed', load)
    return () => {
      mounted = false
      clearInterval(interval)
      window.removeEventListener('ruralb2b:notif-changed', load)
    }
  }, [user, location.pathname])

  useEffect(() => {
    setMobileMenuOpen(false)
    setOpenDropdown(null)
  }, [location.pathname, location.search])

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpenDropdown(null)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSearch = (e) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      window.location.href = '/katalog?search=' + encodeURIComponent(searchQuery.trim())
    }
  }

  const isPathActive = (to) => {
    const [base, query] = to.split('?')
    if (location.pathname === base) {
      return query ? location.search.includes(query) : location.search === ''
    }
    return false
  }

  const groupHasActive = (items) => items.some((item) => isPathActive(item.to))

  const renderDropdown = (id, label, items) => {
    if (!user) return null
    return (
      <div className="relative">
        <button
          onClick={() => setOpenDropdown(openDropdown === id ? null : id)}
          className={`flex items-center gap-1 text-sm font-medium transition-colors hover:text-rural-600 ${
            groupHasActive(items) || openDropdown === id ? 'text-rural-600' : 'text-slate-600'
          }`}
        >
          {label}
          <ChevronDown className={`w-4 h-4 transition-transform ${openDropdown === id ? 'rotate-180' : ''}`} />
        </button>
        {openDropdown === id && (
          <div className="absolute top-full left-0 mt-2 w-56 bg-white border border-slate-200 rounded-xl shadow-rural py-2 z-50">
            {items.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={`block px-4 py-2 text-sm transition-colors hover:bg-rural-50 hover:text-rural-600 ${
                  isPathActive(item.to) ? 'text-rural-600 font-medium bg-rural-50' : 'text-slate-600'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-slate-200 shadow-rural">
      <div className="container flex items-center justify-between px-4 sm:px-6 h-16">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-rural-600 flex items-center justify-center text-white font-bold">
              R
            </div>
            <span className="font-display font-bold text-xl text-slate-900 tracking-tight">
              RuralB2B
            </span>
          </Link>
        </div>

        {/* Desktop nav + search */}
        <div className="hidden md:flex items-center gap-6" ref={dropdownRef}>
          <div className="flex items-center gap-5 text-sm font-medium text-slate-600">
            <Link
              to="/"
              className={`hover:text-rural-600 transition-colors ${isActive('/') ? 'text-rural-600' : ''}`}
            >
              Beranda
            </Link>
            <Link
              to="/katalog"
              className={`hover:text-rural-600 transition-colors ${isActive('/katalog') ? 'text-rural-600' : ''}`}
            >
              Katalog
            </Link>
            {user && caps.canBuy && renderDropdown('buyer', 'Pembelian', buyerMenu)}
            {user && caps.canSell && renderDropdown('seller', 'Penjualan', sellerMenu)}
            {user && (
              <Link
                to="/ai/chat"
                className={`hover:text-rural-600 transition-colors ${isActive('/ai/chat') || isActive('/ai/chat/plus') ? 'text-rural-600' : ''}`}
              >
                AI Assistant
              </Link>
            )}
          </div>

          {/* Desktop search */}
          <div className="hidden lg:flex items-center">
            <form onSubmit={handleSearch} className="relative w-56">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Cari produk..."
                className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-rural-500 focus:border-rural-500 outline-none text-sm"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </form>
          </div>

          <div className="flex items-center gap-3">
            {user ? (
              <>
                <Link
                  to="/chat"
                  className={`p-2 rounded-xl transition-colors hover:bg-rural-50 hover:text-rural-600 text-slate-600 relative ${
                    isActive('/chat') ? 'text-rural-600 bg-rural-50' : ''
                  }`}
                  title="Pesan Saya"
                >
                  <MessageSquare className="w-5 h-5" />
                </Link>
                <Link
                  to="/notifikasi"
                  className={`p-2 rounded-xl transition-colors hover:bg-rural-50 hover:text-rural-600 text-slate-600 relative ${
                    isActive('/notifikasi') ? 'text-rural-600 bg-rural-50' : ''
                  }`}
                  title="Notifikasi"
                >
                  <Bell className="w-5 h-5" />
                  {unreadCount > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 min-w-[1.1rem] h-5 px-1 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                </Link>
                <div className="relative">
                  <button
                    onClick={() => setOpenDropdown(openDropdown === 'user' ? null : 'user')}
                    className="text-sm font-medium text-slate-600 hover:text-rural-600 transition-colors flex items-center gap-1"
                  >
                    {user.full_name || user.email}
                    <ChevronDown className={`w-4 h-4 transition-transform ${openDropdown === 'user' ? 'rotate-180' : ''}`} />
                  </button>
                  {openDropdown === 'user' && (
                    <div className="absolute top-full right-0 mt-2 w-48 bg-white border border-slate-200 rounded-xl shadow-rural py-2 z-50">
                      <Link
                        to="/profil-bisnis"
                        className="block px-4 py-2 text-sm text-slate-600 hover:bg-rural-50 hover:text-rural-600 transition-colors"
                      >
                        Profil Bisnis
                      </Link>
                      <Link
                        to="/pengaturan-akun"
                        className="block px-4 py-2 text-sm text-slate-600 hover:bg-rural-50 hover:text-rural-600 transition-colors"
                      >
                        Pengaturan Akun
                      </Link>
                      {user?.role === 'admin' && (
                        <Link
                          to="/admin"
                          className="block px-4 py-2 text-sm text-slate-600 hover:bg-rural-50 hover:text-rural-600 transition-colors"
                        >
                          Panel Admin
                        </Link>
                      )}
                    </div>
                  )}
                </div>
                <button
                  onClick={onLogout}
                  className="font-medium rounded-xl transition-colors duration-200 flex items-center justify-center gap-2 border border-slate-300 hover:border-rural-600 hover:bg-rural-50 text-slate-700 hover:text-rural-600 px-3 py-1.5 text-sm"
                >
                  Keluar
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="font-medium rounded-xl transition-colors duration-200 flex items-center justify-center border border-slate-300 hover:border-rural-600 hover:bg-rural-50 text-slate-700 hover:text-rural-600 px-3 py-1.5 text-sm"
                >
                  Masuk
                </Link>
                <Link
                  to="/register"
                  className="font-medium rounded-xl transition-colors duration-200 flex items-center justify-center bg-rural-600 hover:bg-rural-700 text-white px-3 py-1.5 text-sm"
                >
                  Daftar
                </Link>
              </>
            )}
          </div>
        </div>

        {/* Mobile: menu toggle */}
        <div className="md:hidden flex items-center gap-3">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-xl text-slate-600 hover:bg-rural-50 hover:text-rural-600 transition-colors"
            aria-label="Buka menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-t border-slate-200 max-h-[calc(100vh-4rem)] overflow-y-auto">
          <div className="container px-4 py-4 space-y-4">
            <form onSubmit={handleSearch} className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Cari produk..."
                className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-rural-500 outline-none text-sm"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </form>
            <div className="space-y-1">
              {renderMobileLink('/', 'Beranda')}
              {renderMobileLink('/katalog', 'Katalog')}
              {user && caps.canBuy && (
                <>
                  <p className="pt-2 pb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Pembelian</p>
                  {buyerMenu.map((item) => renderMobileLink(item.to, item.label))}
                </>
              )}
              {user && caps.canSell && (
                <>
                  <p className="pt-2 pb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Penjualan</p>
                  {sellerMenu.map((item) => renderMobileLink(item.to, item.label))}
                </>
              )}
              {user && (
                <>
                  <p className="pt-2 pb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Lainnya</p>
                  {renderMobileLink('/ai/chat', 'AI Assistant')}
                  {renderMobileLink('/chat', 'Pesan Saya')}
                  {renderMobileLink('/notifikasi', `Notifikasi${unreadCount > 0 ? ` (${unreadCount})` : ''}`)}
                  {user?.role === 'admin' && renderMobileLink('/admin', 'Panel Admin')}
                  {renderMobileLink('/pengaturan-akun', 'Pengaturan Akun')}
                  {renderMobileLink('/profil-bisnis', 'Profil Bisnis')}
                </>
              )}
            </div>
            {user ? (
              <button
                onClick={onLogout}
                className="w-full py-2 px-4 text-sm font-medium text-slate-600 rounded-xl border border-slate-300 hover:bg-slate-50 transition-colors"
              >
                Keluar
              </button>
            ) : (
              <div className="flex gap-3">
                <Link
                  to="/login"
                  className="flex-1 text-center py-2 px-4 text-sm font-medium text-slate-600 rounded-xl border border-slate-300 hover:bg-slate-50 transition-colors"
                >
                  Masuk
                </Link>
                <Link
                  to="/register"
                  className="flex-1 text-center py-2 px-4 text-sm font-medium text-white bg-rural-600 hover:bg-rural-700 rounded-xl transition-colors"
                >
                  Daftar
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  )

  function isActive(path) {
    return location.pathname === path
  }

  function renderMobileLink(to, label) {
    return (
      <Link
        to={to}
        className={`block px-4 py-2 text-sm font-medium rounded-xl transition-colors ${
          isPathActive(to) ? 'bg-rural-50 text-rural-600' : 'text-slate-600 hover:bg-rural-50 hover:text-rural-600'
        }`}
      >
        {label}
      </Link>
    )
  }
}

export default Navbar
