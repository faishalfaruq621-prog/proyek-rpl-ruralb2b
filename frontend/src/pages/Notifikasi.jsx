import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { notificationService } from '../api/auth'
import { Card, CardBody } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { formatDate } from '../utils/format'
import { Bell, CheckCheck } from 'lucide-react'

const TYPE_BADGE = {
  order: 'default',
  payment: 'success',
  chat: 'primary',
  verification: 'warning',
  account: 'danger',
}

export default function Notifikasi() {
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadNotifications()
  }, [])

  const loadNotifications = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await notificationService.getNotifications({ page: 1, per_page: 50 })
      const data = res.data?.data || {}
      setNotifications(Array.isArray(data.items) ? data.items : [])
    } catch (err) {
      console.error('Gagal memuat notifikasi:', err)
      setError(err.response?.data?.message || 'Gagal memuat notifikasi')
    } finally {
      setLoading(false)
    }
  }

  // Badge Navbar diperbarui segera, bukan menunggu polling 60 detik.
  const syncNavbarBadge = () => {
    window.dispatchEvent(new Event('ruralb2b:notif-changed'))
  }

  const markAll = async () => {
    try {
      await notificationService.markAllRead()
      await loadNotifications()
      syncNavbarBadge()
    } catch (err) {
      console.error('Gagal menandai semua dibaca:', err)
    }
  }

  const markOne = async (id) => {
    try {
      const res = await notificationService.markRead([id])
      await loadNotifications()
      // Badge hanya berubah bila memang ada yang ditandai.
      if ((res.data?.data?.updated || 0) > 0) syncNavbarBadge()
    } catch (err) {
      console.error('Gagal menandai dibaca:', err)
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-rural-600"></div>
          <span className="text-sm text-slate-500">Memuat notifikasi...</span>
        </div>
      </div>
    )
  }

  const unread = notifications.filter((n) => !n.is_read).length

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-3xl">
      <div className="flex flex-wrap justify-between items-center gap-3 mb-6">
        <div>
          <h1 className="font-display font-bold text-2xl text-slate-900">Notifikasi</h1>
          <p className="text-slate-600 text-sm">
            {unread > 0 ? `${unread} belum dibaca` : 'Semua sudah dibaca'}
          </p>
        </div>
        {unread > 0 && (
          <Button size="sm" variant="outline" onClick={markAll} className="border border-slate-300 text-slate-600 hover:border-rural-600 hover:text-rural-600">
            <CheckCheck className="w-4 h-4 mr-1" /> Tandai semua dibaca
          </Button>
        )}
      </div>

      {error && (
        <Card className="p-6 mb-6 border-red-100 bg-red-50">
          <p className="text-sm text-red-700">{error}</p>
        </Card>
      )}

      {notifications.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4 text-slate-400">
            <Bell className="w-8 h-8" />
          </div>
          <h3 className="font-bold text-slate-900 mb-2">Belum ada notifikasi</h3>
          <p className="text-slate-500">
            Aktivitas transaksi, pembayaran, verifikasi, dan pesan akan muncul di sini.
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {notifications.map((notif) => {
            const inner = notif.link ? (
              <Link
                to={notif.link}
                onClick={() => markOne(notif.id)}
                className="block p-4 border rounded-xl bg-white hover:bg-rural-50 border-slate-200 transition-colors"
              >
                <NotifRow notif={notif} />
              </Link>
            ) : (
              <button
                onClick={() => markOne(notif.id)}
                className={`w-full text-left block p-4 border rounded-xl transition-colors ${
                  notif.is_read ? 'bg-white border-slate-100' : 'bg-rural-50 border-rural-200 hover:border-rural-300'
                }`}
              >
                <NotifRow notif={notif} />
              </button>
            )
            return <div key={notif.id}>{inner}</div>
          })}
        </div>
      )}
    </div>
  )
}

function NotifRow({ notif }) {
  return (
    <div className="flex gap-3 items-start">
      <div
        className={`mt-1 w-2 h-2 rounded-full shrink-0 ${
          notif.is_read ? 'bg-slate-200' : 'bg-rural-500'
        }`}
      />
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <p className={`text-sm ${notif.is_read ? 'text-slate-700' : 'font-bold text-slate-900'}`}>
            {notif.title}
          </p>
          <Badge variant={TYPE_BADGE[notif.type] || 'default'} className="text-[10px] uppercase">
            {notif.type}
          </Badge>
        </div>
        <p className="text-xs text-slate-500 mt-0.5">{notif.message}</p>
        <p className="text-[11px] text-slate-400 mt-1">{formatDate(notif.created_at)}</p>
      </div>
      {!notif.is_read && (
        <span className="text-[10px] text-rural-600 font-medium shrink-0"> baru </span>
      )}
    </div>
  )
}
