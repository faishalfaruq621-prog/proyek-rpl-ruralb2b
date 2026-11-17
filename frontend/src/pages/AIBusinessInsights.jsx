import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { Card } from '../components/ui/Card'
import { CardHeader } from '../components/ui/Card'
import { CardBody } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { formatRupiah } from '../utils/format'
import { BarChart3, Truck, Package, Clock, AlertTriangle, Loader2, ArrowRight } from 'lucide-react'
import { aiService } from '../api/ai'

export default function AIBusinessInsights() {
  const { user } = useAuth()
  const { error: toastError, success: toastSuccess } = useToast()

  const [summary, setSummary] = useState(null)
  const [transactions, setTransactions] = useState(null)
  const [products, setProducts] = useState(null)
  const [aiAnalysis, setAiAnalysis] = useState(null)
  const [aiAnalysisError, setAiAnalysisError] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [loading, setLoading] = useState(true)
  const [providerStatus, setProviderStatus] = useState(null)

  useEffect(() => {
    if (!user) return
    // Analisis AI (endpoint /ai/insights/analyze) sengaja TIDAK dipanggil
    // otomatis saat halaman dibuka — hemat kuota Gemini, dijalankan on-demand
    // lewat tombol "Analisis Bisnis".
    ;(async () => {
      await Promise.allSettled([
        fetchAIStatus(),
        fetchSummary(),
        fetchTransactions(),
        fetchProducts(),
      ])
      setLoading(false)
    })()
  }, [user])

  const fetchAIStatus = async () => {
    try {
      const data = await aiService.status()
      setProviderStatus(data.data?.data || {})
    } catch (err) {
      console.error('Gagal memuat status AI:', err)
    }
  }

  const fetchSummary = async () => {
    try {
      const result = await aiService.businessSummary()
      const data = result.data
      if (data.success) setSummary(data)
      else toastError(data.message || 'Gagal memuat ringkasan bisnis')
    } catch (err) {
      toastError('Terjadi kesalahan koneksi')
    }
  }

  const fetchTransactions = async () => {
    try {
      const result = await aiService.businessTransactions()
      const data = result.data
      if (data.success) setTransactions(data)
      else toastError(data.message || 'Gagal memuat analisis transaksi')
    } catch (err) {
      toastError('Terjadi kesalahan koneksi')
    }
  }

  const fetchProducts = async () => {
    try {
      const result = await aiService.businessProducts()
      const data = result.data
      if (data.success) setProducts(data)
      else toastError(data.message || 'Gagal memuat performa produk')
    } catch (err) {
      toastError('Terjadi kesalahan koneksi')
    }
  }

  // Analisis AI dijalankan hanya saat tombol ditekan (on-demand).
  // Guard double-click: abaikan klik berikutnya selama request berjalan.
  const handleAnalyze = async () => {
    if (analyzing) return
    setAnalyzing(true)
    setAiAnalysisError(null)
    try {
      const result = await aiService.businessAnalysis()
      const data = result.data
      if (data.success) {
        setAiAnalysis(data)
        setAiAnalysisError(null)
        toastSuccess('Analisis AI berhasil dibuat')
      } else {
        setAiAnalysisError(data.message || 'Gagal menghasilkan analisis AI')
        setAiAnalysis(null)
      }
    } catch (err) {
      setAiAnalysisError('Terjadi kesalahan koneksi ke layanan AI')
      setAiAnalysis(null)
    } finally {
      setAnalyzing(false)
    }
  }

  if (!user) return null

  const isConfigured = providerStatus && providerStatus.configured

  return (
    <div className="min-h-screen bg-earth-50 py-8">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row gap-6 justify-between items-start mb-8">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="w-5 h-5 text-rural-600" />
              <h1 className="font-display font-bold text-2xl text-slate-900">
                AI Business Insights
              </h1>
            </div>
            <p className="text-slate-600">
              Ringkasan performa bisnis, statistik transaksi, dan rekomendasi
              tindakan untuk UMKM Anda.
            </p>
          </div>
          <Link
            to="/produk/kelola"
            className="text-sm text-rural-600 hover:text-rural-700 flex items-center gap-2"
          >
            <ArrowRight className="w-3 h-3" /> Kelola Produk
          </Link>
        </div>

        {/* Status AI */}
        {!isConfigured && (
          <Card className="mb-6 bg-amber-50 border border-amber-100">
            <CardBody className="p-4">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-600" />
                <div>
                  <h3 className="font-bold text-sm text-amber-800">
                    Fitur AI Belum Aktif
                  </h3>
                  <p className="text-xs text-amber-700">
                    Konfigurasikan GEMINI_API_KEY atau OPENROUTER_API_KEY di
                    backend/.env untuk mengaktifkan analisis AI.
                  </p>
                </div>
              </div>
            </CardBody>
          </Card>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase">Total Produk</p>
                <p className="font-bold text-2xl text-slate-900">
                  {summary?.summary.total_products ?? 0}
                </p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600">
                <Package className="w-5 h-5" />
              </div>
            </div>
          </Card>
          <Card className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase">Total Pesanan</p>
                <p className="font-bold text-2xl text-slate-900">
                  {summary?.summary.total_orders ?? 0}
                </p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center text-amber-600">
                <Clock className="w-5 h-5" />
              </div>
            </div>
          </Card>
          <Card className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase">Total Pendapatan</p>
                <p className="font-bold text-2xl text-slate-900">
                  {formatRupiah(summary?.summary.total_revenue ?? 0)}
                </p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-rural-100 flex items-center justify-center text-rural-600">
                <Truck className="w-5 h-5" />
              </div>
            </div>
          </Card>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-rural-600" />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Top Products */}
            <Card>
              <CardHeader className="flex justify-between items-center">
                <h2 className="font-bold text-lg text-slate-900">
                  Produk Unggulan
                </h2>
              </CardHeader>
              <CardBody className="p-4">
                {summary?.top_products && summary.top_products.length > 0 ? (
                  <div className="space-y-3">
                    {summary.top_products.map((p, i) => (
                      <div key={p.product_id} className="flex gap-3 items-center p-2 bg-white border border-slate-100 rounded-xl">
                        <div className="w-8 h-8 rounded-full bg-rural-100 flex items-center justify-center text-rural-600 font-bold text-xs shrink-0">
                          #{i + 1}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-bold text-slate-900 text-sm">
                            {p.product_name}
                          </h4>
                          <p className="text-xs text-slate-500">
                            Terjual {p.total_quantity} {p.unit}
                          </p>
                        </div>
                        <span className="font-medium text-rural-600 text-sm">
                          {formatRupiah(p.total_revenue)}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500 text-center py-8">
                    Belum ada data produk terlaris.
                  </p>
                )}
              </CardBody>
            </Card>

            {/* Low Performance */}
            <Card>
              <CardHeader className="flex justify-between items-center">
                <h2 className="font-bold text-lg text-slate-900">
                  Perlu Ditingkatkan
                </h2>
              </CardHeader>
              <CardBody className="p-4">
                {summary?.low_performance_products &&
                summary.low_performance_products.length > 0 ? (
                  <div className="space-y-3">
                    {summary.low_performance_products.map((p) => (
                      <div key={p.product_id} className="flex gap-3 items-center p-2 bg-amber-50 border border-amber-100 rounded-xl">
                        <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center text-amber-600 font-bold text-xs shrink-0">
                          <AlertTriangle className="w-3 h-3" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-bold text-slate-900 text-sm">
                            {p.product_name}
                          </h4>
                          <p className="text-xs text-slate-500">
                            Stok {p.available_quantity} {p.unit}, belum terjual
                          </p>
                        </div>
                        <span className="font-medium text-amber-700 text-sm">
                          {formatRupiah(p.price)}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500 text-center py-8">
                    Semua produk berperforma baik atau belum ada data.
                  </p>
                )}
              </CardBody>
            </Card>

            {/* Transactions */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <h2 className="font-bold text-lg text-slate-900">
                  Tren Transaksi
                </h2>
              </CardHeader>
              <CardBody className="p-4">
                {transactions?.monthly_revenue && transactions.monthly_revenue.length > 0 ? (
                  <div className="space-y-3">
                    {transactions.monthly_revenue.map((m) => (
                      <div key={m.month} className="flex justify-between items-center p-2 bg-white border border-slate-100 rounded-xl">
                        <div>
                          <h4 className="font-bold text-slate-900 text-sm">
                            {m.month}
                          </h4>
                          <p className="text-xs text-slate-500">
                            {m.order_count} pesanan
                          </p>
                        </div>
                        <span className="font-medium text-rural-600 text-sm">
                          {formatRupiah(m.revenue)}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500 text-center py-8">
                    Belum ada data transaksi.
                  </p>
                )}
              </CardBody>
            </Card>

            {/* Product Performance */}
            <Card>
              <CardHeader className="flex justify-between items-center">
                <h2 className="font-bold text-lg text-slate-900">
                  Performa Produk
                </h2>
                <Button size="sm" variant="outline" asChild>
                  <Link to="/produk/kelola">Kelola Semua</Link>
                </Button>
              </CardHeader>
              <CardBody className="p-4">
                {products?.products && products.products.length > 0 ? (
                  <div className="space-y-3">
                    {products.products.slice(0, 8).map((p) => (
                      <div key={p.product_id} className="flex gap-3 items-start p-3 bg-white border border-slate-100 rounded-xl">
                        <div className="w-10 h-10 bg-slate-100 rounded flex items-center justify-center shrink-0">
                          <Package className="w-4 h-4 text-slate-500" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-bold text-slate-900 text-sm">
                            {p.product_name}
                          </h4>
                          <div className="flex gap-2 text-xs text-slate-600 mt-1">
                            <span>{p.status}</span>
                            <span>•</span>
                            <span>{p.available_quantity} {p.unit}</span>
                          </div>
                          <div className="mt-1 flex gap-2 text-xs">
                            <span className="font-medium text-slate-900">
                              Terjual {p.total_sold}
                            </span>
                            <span className="text-rural-600">
                              {formatRupiah(p.total_revenue)}
                            </span>
                          </div>
                          {p.needs_attention && (
                            <Badge variant="warning" className="text-[10px] mt-1">
                              Perlu Perhatian
                            </Badge>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500 text-center py-8">
                    Belum ada data produk.
                  </p>
                )}
              </CardBody>
            </Card>
          </div>
        )}

        {/* AI Analysis Section — on-demand: hanya dipanggil lewat tombol */}
        {isConfigured ? (
          analyzing ? (
            <Card className="mt-8">
              <CardBody className="p-5 flex items-center justify-center">
                <Loader2 className="w-5 h-5 animate-spin text-rural-600" />
                <span className="ml-2 text-sm text-slate-500">
                  Menghasilkan analisis AI (memerlukan beberapa detik)...
                </span>
              </CardBody>
            </Card>
          ) : aiAnalysisError ? (
            <Card className="mt-8 bg-red-50 border border-red-100">
              <CardBody className="p-5">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <h3 className="font-bold text-sm text-red-800">
                      Analisis AI Tidak Tersedia
                    </h3>
                    <p className="text-sm text-red-700 mt-1">
                      {aiAnalysisError}
                    </p>
                    <Button
                      size="sm"
                      variant="outline"
                      className="mt-3"
                      onClick={handleAnalyze}
                    >
                      <BarChart3 className="w-3 h-3" /> Analisis Ulang
                    </Button>
                  </div>
                </div>
              </CardBody>
            </Card>
          ) : aiAnalysis ? (
            <Card className="mt-8 bg-rural-50 border border-rural-100">
              <CardHeader className="p-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <BarChart3 className="w-4 h-4 text-rural-600" />
                      <h2 className="font-bold text-lg text-rural-900">
                        Analisis &amp; Rekomendasi Bisnis AI
                      </h2>
                    </div>
                    {aiAnalysis.provider && (
                      <p className="text-xs text-slate-500 mt-1">
                        Dihasilkan oleh {aiAnalysis.provider} ({aiAnalysis.model})
                      </p>
                    )}
                  </div>
                  <Button size="sm" variant="outline" onClick={handleAnalyze}>
                    <BarChart3 className="w-3 h-3" /> Analisis Ulang
                  </Button>
                </div>
              </CardHeader>
              <CardBody className="p-5">
                <div className="prose prose-sm text-slate-700 max-w-none">
                  {(aiAnalysis.analysis || '').split('\n\n').map((block, idx) => (
                    <div key={idx} className="mb-4">
                      {block.startsWith('- ') || block.startsWith('• ') ? (
                        <ul className="list-disc list-inside space-y-1 text-slate-700">
                          {block.split('\n').map((line, li) => (
                            <li key={li} className={li === 0 ? '' : 'ml-4'}>
                              {line.replace(/^[-•]\s*/, '')}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className={idx === 0 ? 'font-bold text-slate-900 mb-2' : 'text-slate-700 mb-2'}>
                          {block}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>
          ) : (
            <Card className="mt-8">
              <CardBody className="p-5 flex flex-col items-center text-center">
                <div className="w-12 h-12 rounded-2xl bg-rural-100 flex items-center justify-center text-rural-600 mb-3">
                  <BarChart3 className="w-6 h-6" />
                </div>
                <h3 className="font-bold text-slate-900">
                  Analisis &amp; Rekomendasi Bisnis AI
                </h3>
                <p className="text-sm text-slate-600 mt-1 max-w-md">
                  Gemini akan menganalisis performa produk, tren transaksi, dan
                  stok bisnis Anda, lalu memberikan rekomendasi tindakan.
                </p>
                <Button className="mt-4" onClick={handleAnalyze}>
                  <BarChart3 className="w-4 h-4" /> Analisis Bisnis
                </Button>
              </CardBody>
            </Card>
          )
        ) : (
          <Card className="mt-8 bg-amber-50 border border-amber-100">
            <CardBody className="p-5">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-bold text-sm text-amber-800">
                    Fitur AI Belum Aktif
                  </h3>
                  <p className="text-sm text-amber-700 mt-1">
                    Konfigurasikan GEMINI_API_KEY atau OPENROUTER_API_KEY di
                    backend/.env untuk mengaktifkan analisis AI bisnis.
                  </p>
                </div>
              </div>
            </CardBody>
          </Card>
        )}
      </div>
    </div>
  )
}
