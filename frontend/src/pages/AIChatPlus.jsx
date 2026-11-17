import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { Card, CardHeader, CardBody, CardFooter } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Button } from '../components/ui/Button'
import { Send, Menu, Bot, MessageCircle, Loader2, BarChart3, X } from 'lucide-react'

export default function AIChatPlus() {
  const { user } = useAuth()
  const { error: toastError, success: toastSuccess } = useToast()
  const navigate = useNavigate()

  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [providerStatus, setProviderStatus] = useState(null)
  const [businessContext, setBusinessContext] = useState(null)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    if (!user) {
      navigate('/login', { replace: true })
      return
    }
    fetchAIStatus()
    fetchBusinessContext()
    if (messages.length === 0) {
      setMessages([
        {
          role: 'assistant',
          content:
            'Halo! Saya asisten bisnis UMKM RuralB2B. Saya dapat membantu menganalisis penjualan, produk terlaris, strategi harga, dan rekomendasi pengembangan usaha Anda. Apa yang ingin Anda analisis hari ini?',
        },
      ])
    }
  }, [user, navigate, messages.length])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const fetchAIStatus = async () => {
    try {
      const res = await fetch('/api/ai/status', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('ruralb2b_token')}`,
        },
      })
      const data = await res.json()
      setProviderStatus(data.data || {})
    } catch (err) {
      console.error('Gagal memuat status AI:', err)
    }
  }

  const fetchBusinessContext = async () => {
    try {
      const res = await fetch('/api/ai/insights/summary', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('ruralb2b_token')}`,
        },
      })
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          setBusinessContext(data)
        }
      }
    } catch (err) {
      console.error('Gagal memuat konteks bisnis:', err)
    }
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim()) return
    if (!localStorage.getItem('ruralb2b_token')) {
      toastError('Sesi tidak valid. Silakan login kembali.')
      navigate('/login')
      return
    }

    const userMessage = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/api/ai/chat/plus', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('ruralb2b_token')}`,
        },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          business_context: businessContext,
          temperature: 0.7,
        }),
      })
      const data = await res.json()

      if (data.success) {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: data.content },
        ])
        toastSuccess('Analisis diterima dari ' + (data.provider || 'AI'))
      } else {
        toastError(data.message || 'Gagal mendapatkan analisis dari AI')
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content:
              'Maaf, saya sedang mengalami gangguan. Silakan coba lagi nanti.',
          },
        ])
      }
    } catch (err) {
      toastError('Terjadi kesalahan koneksi ke layanan AI')
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            'Maaf, saya tidak dapat terhubung ke layanan AI saat ini. Silakan coba lagi nanti.',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  if (!user) return null

  const isConfigured = providerStatus && providerStatus.configured

  return (
    <div className="min-h-screen bg-earth-50 py-8">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-4xl">
        <div className="flex flex-col lg:flex-row gap-6 justify-between items-start mb-8">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="w-5 h-5 text-rural-600" />
              <h1 className="font-display font-bold text-2xl text-slate-900">
                Chatbot Plus
              </h1>
            </div>
            <p className="text-slate-600">
              Asisten bisnis untuk UMKM. Analisis penjualan, produk terlaris,
              strategi harga, dan rekomendasi pengembangan usaha berdasarkan
              data aktual.
            </p>
          </div>
          <Link
            to="/dashboard"
            className="text-sm text-rural-600 hover:text-rural-700 flex items-center gap-2"
          >
            <Menu className="w-3 h-3" /> Kembali ke Dashboard
          </Link>
        </div>

        {/* Status AI */}
        <Card className="mb-6">
          <CardHeader className="p-4">
            <div className="flex items-center gap-3">
              <Bot className="w-5 h-5 text-rural-600" />
              <div>
                <h3 className="font-bold text-sm text-slate-900">
                  Status Asisten Bisnis AI
                </h3>
                <p className="text-xs text-slate-500">
                  {isConfigured
                    ? `Siap menganalisis (${providerStatus.provider})`
                    : 'Belum dikonfigurasi'}
              </p>
              </div>
              {!isConfigured && (
                <span className="ml-auto px-2 py-1 text-xs font-medium bg-red-50 text-red-700 rounded-full">
                  Perlu API Key
                </span>
              )}
            </div>
          </CardHeader>
          <CardBody className="p-4">
            {!isConfigured && (
              <div className="bg-amber-50 border border-amber-100 rounded-xl p-4">
                <p className="text-sm text-amber-800 mb-2">
                  Fitur AI belum aktif. Administrator perlu mengatur
                  <code className="font-mono text-xs">GEMINI_API_KEY</code>
                  atau
                  <code className="font-mono text-xs">OPENROUTER_API_KEY</code>
                  di backend/.env.
                </p>
              </div>
            )}
            {businessContext && businessContext.success && (
              <div className="mt-4 bg-rural-50 border border-rural-100 rounded-xl p-4">
                <p className="text-xs text-rural-700 font-medium mb-1">
                  Konteks Bisnis Aktual (dari database)
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-500">Total Produk:</span>
                    <span className="font-medium text-slate-900 block">
                      {businessContext.summary.total_products}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Total Pesanan:</span>
                    <span className="font-medium text-slate-900 block">
                      {businessContext.summary.total_orders}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Pendapatan:</span>
                    <span className="font-medium text-slate-900 block">
                      {businessContext.summary.total_revenue}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Selesai:</span>
                    <span className="font-medium text-slate-900 block">
                      {businessContext.summary.completed_orders}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </CardBody>
        </Card>

        {/* Chat Area */}
        <Card className="flex flex-col h-[600px]">
          <CardHeader>
            <h2 className="font-bold text-lg text-slate-900">
              Konsultasi Bisnis
            </h2>
          </CardHeader>
          <CardBody className="flex-1 overflow-y-auto p-4 space-y-4" ref={messagesEndRef}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-3 max-w-[85%] ${
                  msg.role === 'user'
                    ? 'ml-auto justify-end'
                    : 'mr-auto justify-start'
                }`}
              >
                <div
                  className={`p-3 rounded-2xl ${
                    msg.role === 'user'
                      ? 'bg-rural-600 text-white'
                      : 'bg-white border border-slate-200 text-slate-900'
                  } shadow-sm`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>
                {msg.role === 'assistant' && loading && idx === messages.length - 1 && (
                  <div className="flex items-center gap-1 text-slate-400 text-xs mt-1">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    <span>Menganalisis...</span>
                  </div>
                )}
              </div>
            ))}
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-40 text-slate-500">
                <BarChart3 className="w-8 h-8 mb-2" />
                <p>Mulai konsultasi bisnis dengan mengajukan pertanyaan.</p>
              </div>
            )}
          </CardBody>
          <CardFooter className="p-4">
            <form onSubmit={handleSend} className="flex gap-3">
              <Input
                placeholder="Contoh: Produk apa yang terlaris bulan ini?"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading || !isConfigured}
                className="flex-1"
              />
              <Button
                type="submit"
                disabled={loading || !input.trim() || !isConfigured}
                className="bg-rural-600 hover:bg-rural-700 text-white"
              >
                <Send className="w-4 h-4" />
              </Button>
              {!isConfigured && (
                <Button variant="outline" size="sm" disabled>
                  <X className="w-3 h-3" /> Dinonaktifkan
                </Button>
              )}
            </form>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}
