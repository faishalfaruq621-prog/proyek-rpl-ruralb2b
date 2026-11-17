import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { Card, CardHeader, CardBody, CardFooter } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Button } from '../components/ui/Button'
import { aiService } from '../api/ai'
import { Send, Menu, Bot, MessageCircle, Loader2, X } from 'lucide-react'

export default function AIChatStandard() {
  const { user } = useAuth()
  const { error: toastError, success: toastSuccess } = useToast()
  const navigate = useNavigate()

  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content:
        'Halo! Saya asisten AI RuralB2B. Ada yang bisa saya bantu tentang marketplace B2B UMKM pedesaan Indonesia?',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [providerStatus, setProviderStatus] = useState(null)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    if (!user) {
      navigate('/login', { replace: true })
      return
    }
    fetchAIStatus()
  }, [user, navigate])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const fetchAIStatus = async () => {
    try {
      const res = await aiService.status()
      setProviderStatus(res.data.data || {})
    } catch (err) {
      console.error('Gagal memuat status AI:', err)
    }
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim()) return
    if (!user) {
      toastError('Sesi tidak valid. Silakan login kembali.')
      navigate('/login')
      return
    }

    const userMessage = { id: Date.now(), role: 'user', content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const res = await aiService.chatStandard([...messages, userMessage])
      if (res.data.success) {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            role: 'assistant',
            content: res.data.content,
          },
        ])
        toastSuccess('Balasan diterima dari ' + (res.data.provider || 'AI'))
      } else {
        toastError(res.data.message || 'Gagal mendapatkan balasan dari AI')
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
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
          id: Date.now() + 1,
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
            <h1 className="font-display font-bold text-2xl text-slate-900">
              Chatbot Standard
            </h1>
            <p className="text-slate-600">
              Tanya apapun tentang penggunaan RuralB2B, katalog produk,
              pemesanan, dan pembayaran.
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
                  Status Asisten AI
                </h3>
                <p className="text-xs text-slate-500">
                  {isConfigured
                    ? `Siap melayani (${providerStatus.provider})`
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
                <p className="text-xs text-amber-600">
                  Tanpa konfigurasi, chatbot akan menampilkan pesan keterbatasan.
                </p>
              </div>
            )}
          </CardBody>
        </Card>

        {/* Chat Area */}
        <Card className="flex flex-col h-[600px]">
          <CardHeader>
            <h2 className="font-bold text-lg text-slate-900">
              Percakapan
            </h2>
          </CardHeader>
          <CardBody className="flex-1 overflow-y-auto p-4 space-y-4" ref={messagesEndRef}>
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 max-w-[85%] ${
                  msg.role === 'user'
                    ? 'ml-auto justify-end'
                    : 'mr-auto justify-start'
                }`}
              >
                <div
                  className={`p-3 rounded-2xl ${
                    msg.role === 'user'
                      ? 'bg-rural-600 text-white rounded-tr-none'
                      : 'bg-white border border-slate-200 text-slate-900 rounded-tl-none'
                  } shadow-sm`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>
                {msg.role === 'assistant' && loading && msg.id === messages[messages.length - 1]?.id && (
                  <div className="flex items-center gap-1 text-slate-400 text-xs mt-1">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    <span>Mengetik...</span>
                  </div>
                )}
              </div>
            ))}
          </CardBody>
          <CardFooter className="p-4">
            <form onSubmit={handleSend} className="flex gap-3">
              <Input
                placeholder="Ketik pertanyaan Anda di sini..."
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
