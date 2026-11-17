import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { chatService } from '../api/auth'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { formatDate } from '../utils/format'
import { getCapabilities } from '../utils/capabilities'
import { useAuth } from '../context/AuthContext'
import { MessageSquare, MessageCircle } from 'lucide-react'

export default function ChatList() {
  const location = useLocation()
  const { user } = useAuth()

  // Pembeli dibuka langsung tampil bersih tanpa switch; Seller juga bisa.
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadConversations()
  }, [])

  const loadConversations = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await chatService.getConversations({ page: 1, per_page: 50 })
      const data = res.data?.data || {}
      setConversations(Array.isArray(data.items) ? data.items : [])
    } catch (err) {
      console.error('Gagal memuat percakapan:', err)
      setError(err.response?.data?.message || 'Gagal memuat percakapan')
    } finally {
      setLoading(false)
    }
  }

  const counterpart = (conv) => {
    if (!user) return null
    return String(user.id) === String(conv.buyer?.id) ? conv.seller : conv.buyer
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-rural-600"></div>
          <span className="text-sm text-slate-500">Memuat percakapan...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-3xl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="font-display font-bold text-2xl text-slate-900">Pesan Saya</h1>
          <p className="text-slate-600 text-sm">
            Percakapan dengan pembeli/penjual terkait produk dan pesanan.
          </p>
        </div>
      </div>

      {error && (
        <Card className="p-6 mb-6 border-red-100 bg-red-50">
          <p className="text-sm text-red-700">{error}</p>
        </Card>
      )}

      {conversations.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4 text-slate-400">
            <MessageSquare className="w-8 h-8" />
          </div>
          <h3 className="font-bold text-slate-900 mb-2">Belum ada percakapan</h3>
          <p className="text-slate-500 mb-6">
            Mulai percakapan dari halaman produk atau detail pesanan.
          </p>
          <Button asChild variant="outline">
            <Link to="/katalog">Jelajahi Katalog</Link>
          </Button>
        </Card>
      ) : (
        <div className="space-y-3">
          {conversations.map((conv) => {
            const counterpartUser = counterpart(conv)
            const context =
              conv.product?.product_name ||
              (conv.order_id ? `Pesanan #${conv.order_id}` : 'Tidak ada konteks')
            return (
              <Card
                key={conv.id}
                className="hover:border-rural-200 transition-colors cursor-pointer"
              >
                <Link
                  to={`/chat/${conv.id}`}
                  className="flex items-center gap-4 p-4"
                >
                  <div className="w-10 h-10 rounded-xl bg-rural-100 text-rural-600 flex items-center justify-center font-bold shrink-0">
                    {counterpartUser?.business_name?.charAt(0) ||
                      counterpartUser?.full_name?.charAt(0) || 'C'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-center gap-2">
                      <p className="font-bold text-slate-900 text-sm truncate">
                        {counterpartUser?.business_name ||
                          counterpartUser?.full_name ||
                          'Percakapan'}
                        {counterpartUser?.id === conv.seller?.id ? (
                          <Badge variant="default" className="text-[10px] ml-2">
                            penjual
                          </Badge>
                        ) : (
                          <Badge variant="success" className="text-[10px] ml-2">
                            pembeli
                          </Badge>
                        )}
                      </p>
                      {conv.last_message && (
                        <span className="text-[11px] text-slate-400 shrink-0">
                          {formatDate(conv.last_message.created_at)}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 truncate">
                      {conv.last_message
                        ? conv.last_message.body
                        : 'Belum ada pesan.'}
                    </p>
                    <p className="text-[11px] text-rural-600 truncate">konteks: {context}</p>
                  </div>
                  <MessageCircle className="w-4 h-4 text-slate-300 shrink-0" />
                </Link>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
