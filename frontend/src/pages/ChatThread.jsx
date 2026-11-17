import { useState, useEffect, useRef } from 'react'
import { Link, useParams } from 'react-router-dom'
import { chatService } from '../api/auth'
import { Card, CardBody } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { formatDate } from '../utils/format'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { ArrowRight, Send } from 'lucide-react'

export default function ChatThread() {
  const { id } = useParams()
  const { user } = useAuth()
  const { error: toastError } = useToast()
  const [conversation, setConversation] = useState(null)
  const [messages, setMessages] = useState([])
  const [body, setBody] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [notFound, setNotFound] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    let mounted = true
    const load = async () => {
      setLoading(true)
      setNotFound(false)
      try {
        const [convRes, msgRes] = await Promise.all([
          chatService.getConversation(id),
          chatService.getMessages(id, { page: 1, per_page: 100 }),
        ])
        if (!mounted) return
        setConversation(convRes.data?.data?.conversation || null)
        setMessages(
          Array.isArray(msgRes.data?.data?.items) ? msgRes.data.data.items : []
        )
      } catch (err) {
        console.error('Gagal memuat percakapan:', err)
        if (err.response?.status === 404) setNotFound(true)
        else toastError(err.response?.data?.message || 'Gagal memuat percakapan')
      } finally {
        if (mounted) setLoading(false)
      }
    }
    load()
    // Polling ringan: pesan masuk dari pihak lawan tampil tanpa refresh manual.
    const interval = setInterval(async () => {
      if (document.hidden) return
      try {
        const res = await chatService.getMessages(id, { page: 1, per_page: 100 })
        setMessages(Array.isArray(res.data?.data?.items) ? res.data.data.items : [])
      } catch {
        // hening; coba lagi siklus berikutnya
      }
    }, 10000)
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!body.trim() || sending) return
    setSending(true)
    try {
      const res = await chatService.sendMessage(id, { body: body.trim() })
      const sent = res.data?.data?.message
      if (sent) setMessages((prev) => [...prev, sent])
      setBody('')
    } catch (err) {
      toastError(err.response?.data?.message || 'Gagal mengirim pesan')
    } finally {
      setSending(false)
    }
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

  if (notFound || !conversation) {
    return (
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-16">
          <h2 className="font-bold text-slate-900 mb-2">Percakapan tidak ditemukan</h2>
          <p className="text-slate-500 mb-6 text-sm">Percakapan tidak ada atau bukan milik Anda.</p>
          <Button asChild variant="outline">
            <Link to="/chat">
              <ArrowRight className="w-4 h-4 mr-2" style={{ transform: 'rotate(180deg)' }} /> Pesan Saya
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  const isBuyer = String(user?.id) === String(conversation.buyer?.id)
  const counterpart = isBuyer ? conversation.seller : conversation.buyer

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-3xl">
      <Button asChild variant="outline" size="sm" className="mb-3">
        <Link to="/chat">
          <ArrowRight className="w-4 h-4" style={{ transform: 'rotate(180deg)' }} /> Daftar Percakapan
        </Link>
      </Button>

      <Card className="flex flex-col min-h-[60vh]">
        <CardBody className="border-b border-slate-100 p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-rural-100 text-rural-600 flex items-center justify-center font-bold shrink-0">
            {counterpart?.business_name?.charAt(0) || counterpart?.full_name?.charAt(0) || 'C'}
          </div>
          <div className="min-w-0">
            <p className="font-bold text-slate-900 truncate">
              {counterpart?.business_name || counterpart?.full_name || 'Percakapan'}
            </p>
            <p className="text-xs text-slate-500 truncate">
              {conversation.product
                ? `Produk: ${conversation.product.product_name}`
                : conversation.order_id
                  ? `Pesanan #${conversation.order_id}`
                  : ''}
            </p>
          </div>
          {/* Tautan konteks: ke produk untuk buyer, ke detail pesanan bila ada */}
          <Button asChild variant="outline" size="sm" className="ml-auto shrink-0">
            {conversation.order_id ? (
              <Link to={`${isBuyer ? '/pesanan/' : '/seller/pesanan/'}${conversation.order_id}`}>
                {isBuyer ? 'Buka Pesanan' : 'Buka Pesanan Masuk'}
              </Link>
            ) : conversation.product ? (
              <Link to={`/produk/${conversation.product.id}`}>
                Lihat Produk
              </Link>
            ) : (
              <span>Detail</span>
            )}
          </Button>
        </CardBody>

        <CardBody className="flex-1 overflow-y-auto p-4 space-y-2">
          {messages.length === 0 ? (
            <p className="text-sm text-slate-400 text-center py-10">
              Belum ada pesan. Tulis pesan pertama di bawah.
            </p>
          ) : (
            messages.map((msg) => {
              const mine = String(user?.id) === String(msg.sender?.id)
              return (
                <div key={msg.id} className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-[75%] rounded-2xl px-4 py-2 text-sm ${
                      mine
                        ? 'bg-rural-600 text-white'
                        : 'bg-slate-100 text-slate-800'
                    }`}
                  >
                    <p className="leading-relaxed whitespace-pre-wrap break-words">{msg.body}</p>
                    <p className={`text-[10px] mt-1 ${mine ? 'text-rural-100' : 'text-slate-400'}`}>
                      {msg.sender?.role === 'admin' ? 'Admin' : msg.sender?.full_name} · {formatDate(msg.created_at)}
                    </p>
                  </div>
                </div>
              )
            })
          )}
          <div ref={bottomRef} />
        </CardBody>

        <CardBody className="border-t border-slate-100 p-3">
          <form onSubmit={handleSend} className="flex gap-2 items-center">
            <input
              type="text"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Tulis pesan..."
              className="flex-1 border border-slate-200 rounded-xl px-4 py-2 text-sm focus:ring-2 focus:ring-rural-500 outline-none"
            />
            <Button type="submit" disabled={sending || !body.trim()} className="bg-rural-600 hover:bg-rural-700 text-white px-4">
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  )
}
