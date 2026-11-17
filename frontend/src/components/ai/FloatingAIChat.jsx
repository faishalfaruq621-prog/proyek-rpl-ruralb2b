import { useState, useEffect, useRef, useCallback } from 'react'
import { useAuth } from '../../context/AuthContext'
import { useToast } from '../../context/ToastContext'
import { aiService } from '../../api/ai'
import { Bot, Send, X, Maximize, Minimize, MessageCircle, Loader2, ChevronRight } from 'lucide-react'

const EXAMPLE_QUESTIONS = [
  'Cara mendaftar sebagai penjual?',
  'Bagaimana cara checkout?',
  'Produk apa saja yang tersedia?',
]

export function FloatingAIChat() {
  const { user, logout } = useAuth()
  const { error: toastError } = useToast()
  const [isOpen, setIsOpen] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
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
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim()) return

    if (!user) {
      toastError('Silakan login terlebih dahulu untuk menggunakan chatbot AI.')
      return
    }

    const userMessage = { id: Date.now(), role: 'user', content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const res = await aiService.chatStandard([
        ...messages,
        userMessage,
      ])
      if (res.data.success) {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            role: 'assistant',
            content: res.data.content,
          },
        ])
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

  const handleExampleClick = (question) => {
    setInput(question)
  }

  if (!user) return null

  return (
    <div className="fixed bottom-6 right-6 z-[100]">
      {/* Floating toggle button */}
      {!isOpen && !isMinimized && (
        <button
          onClick={() => setIsOpen(true)}
          className="w-14 h-14 bg-rural-600 hover:bg-rural-700 text-white rounded-full flex items-center justify-center shadow-rural-lg transition-all transform hover:scale-105"
          aria-label="Buka RuralB2B AI Assistant"
        >
          <Bot className="w-7 h-7" />
        </button>
      )}

      {/* Minimized state */}
      {!isOpen && isMinimized && (
        <button
          onClick={() => setIsOpen(true)}
          className="w-14 h-14 bg-rural-600 hover:bg-rural-700 text-white rounded-full flex items-center justify-center shadow-rural-lg transition-all"
          aria-label="Buka RuralB2B AI Assistant"
        >
          <Bot className="w-7 h-7" />
        </button>
      )}

      {/* Chat window */}
      {isOpen && (
        <div className="w-[380px] h-[540px] bg-white rounded-2xl shadow-rural-lg flex flex-col border border-slate-200 transform transition-all">
          {/* Header */}
          <div className="bg-rural-600 text-white rounded-t-2xl px-5 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-rural-500 rounded-lg flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-white leading-tight">
                  RuralB2B AI
                </h3>
                <p className="text-xs text-rural-200">Asisten Marketplace</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsMinimized(true)}
                className="w-8 h-8 bg-rural-500 rounded flex items-center justify-center text-white hover:bg-rural-400 transition-colors"
                aria-label="Minimize"
              >
                <Minimize className="w-4 h-4" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="w-8 h-8 bg-rural-500 rounded flex items-center justify-center text-white hover:bg-rural-400 transition-colors"
                aria-label="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Messages area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={messagesEndRef}>
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[80%] p-3 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-rural-600 text-white rounded-tr-none'
                      : 'bg-slate-100 text-slate-900 rounded-tl-none'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-slate-100 p-3 rounded-lg rounded-tl-none">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 text-rural-600 animate-spin" />
                    <span className="text-xs text-slate-500">Mengetik...</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Example questions (shown when no messages except welcome) */}
          {messages.length === 1 && !loading && (
            <div className="p-4 border-t border-slate-100">
              <p className="text-xs font-medium text-slate-500 mb-3">
                Contoh pertanyaan:
              </p>
              <div className="space-y-2">
                {EXAMPLE_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleExampleClick(q)}
                    className="w-full text-left px-3 py-2 rounded-lg bg-slate-50 hover:bg-rural-50 text-xs text-slate-600 border border-slate-200 transition-colors"
                  >
                    <ChevronRight className="w-3 h-3 mr-2 text-rural-600" />
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input area */}
          <div className="p-4 border-t border-slate-200 bg-slate-50">
            <form onSubmit={handleSend} className="flex gap-2">
              <input
                type="text"
                placeholder="Ketik pesan Anda..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
                className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-rural-500 focus:border-rural-500 outline-none text-sm bg-white"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="bg-rural-600 hover:bg-rural-700 text-white px-4 py-2.5 rounded-xl flex items-center justify-center disabled:opacity-50 disabled:pointer-events-none transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
