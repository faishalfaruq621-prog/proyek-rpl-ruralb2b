import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { Card } from '../components/ui/Card'
import { CardHeader } from '../components/ui/Card'
import { CardBody } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { formatRupiah } from '../utils/format'
import { Search, Truck, Package, ArrowRight, Loader2 } from 'lucide-react'
import { aiService } from '../api/ai'

export default function AIProductRecommendation() {
  const { user } = useAuth()
  const { error: toastError, success: toastSuccess } = useToast()

  const [query, setQuery] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(false)
  const [providerStatus, setProviderStatus] = useState(null)

  useEffect(() => {
    if (!user) return
    fetchAIStatus()
  }, [user])

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

  const fetchRecommendations = async () => {
    setLoading(true)
    try {
      const result = await aiService.recommendations({
        buyer_need: query || undefined,
        category_id: categoryId || undefined,
      })
      const data = result.data

      if (data.success) {
        setRecommendations(data.recommendations || [])
        toastSuccess(
          data.total_found
            ? `${data.total_found} rekomendasi ditemukan`
            : 'Tidak ada rekomendasi yang cocok'
        )
      } else {
        toastError(data.message || 'Gagal mendapatkan rekomendasi')
      }
    } catch (err) {
      toastError('Terjadi kesalahan koneksi ke layanan AI')
    } finally {
      setLoading(false)
    }
  }

  const fetchByCategory = async (id) => {
    setCategoryId(String(id))
    setLoading(true)
    try {
      const result = await aiService.recommendationsByCategory(Number(id), {
        limit: 20,
      })
      const data = result.data
      if (data.success) {
        setRecommendations(data.recommendations || [])
      } else {
        toastError(data.message || 'Gagal mendapatkan rekomendasi kategori')
      }
    } catch (err) {
      toastError('Terjadi kesalahan koneksi')
    } finally {
      setLoading(false)
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
              <Package className="w-5 h-5 text-rural-600" />
              <h1 className="font-display font-bold text-2xl text-slate-900">
                AI Product Recommendation
              </h1>
            </div>
            <p className="text-slate-600">
              Dapatkan rekomendasi produk berdasarkan kebutuhan, kategori,
              harga, dan stok aktual dari mitra UMKM RuralB2B.
            </p>
          </div>
          <Link
            to="/katalog"
            className="text-sm text-rural-600 hover:text-rural-700 flex items-center gap-2"
          >
            <ArrowRight className="w-3 h-3" /> Lihat Katalog Lengkap
          </Link>
        </div>

        {/* Status AI */}
        <Card className="mb-6">
          <CardHeader className="p-4">
            <div className="flex items-center gap-3">
              <Search className="w-5 h-5 text-rural-600" />
              <div>
                <h3 className="font-bold text-sm text-slate-900">
                  Status Rekomendasi AI
                </h3>
                <p className="text-xs text-slate-500">
                  {isConfigured
                    ? `Aktif (${providerStatus.provider})`
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
                <p className="text-sm text-amber-800">
                  Fitur rekomendasi AI belum aktif. Konfigurasikan API Key di
                  backend/.env.
                </p>
              </div>
            )}
          </CardBody>
        </Card>

        {/* Search / Filter */}
        <Card className="mb-8">
          <CardBody className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
                <Input
                  placeholder="Contoh: sayuran segar, beras organik, buah..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <div>
                <label className="label mb-2">Kategori ID (opsional)</label>
                <Input
                  type="number"
                  placeholder="1"
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                />
              </div>
              <div className="flex items-end">
                <Button
                  onClick={fetchRecommendations}
                  disabled={loading || !isConfigured}
                  className="w-full bg-rural-600 hover:bg-rural-700 text-white"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      Mencari...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4 mr-2" /> Cari Rekomendasi
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Results */}
        {loading ? (
          <div className="flex justify-center py-20">
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="w-8 h-8 animate-spin text-rural-600" />
              <p className="text-sm text-slate-500">Mencari rekomendasi...</p>
            </div>
          </div>
        ) : recommendations.length === 0 && !loading ? (
          <Card className="p-12 text-center">
            <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4 text-slate-400">
              <Package className="w-8 h-8" />
            </div>
            <h3 className="font-bold text-slate-900 mb-2">
              Belum ada rekomendasi
            </h3>
            <p className="text-slate-500 mb-6">
              Masukkan kebutuhan produk atau pilih kategori untuk mencari
              rekomendasi.
            </p>
            <Button asChild size="sm" variant="outline" className="w-full">
              <Link to="/katalog">Lihat Semua Produk</Link>
            </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {recommendations.map((p) => (
              <Link to={`/produk/${p.product_id}`} key={p.product_id}>
                <Card className="hover:border-rural-200 transition-border">
                <div className="h-48 bg-slate-100 flex items-center justify-center overflow-hidden mb-4 relative">
                  <div className="w-full h-full flex items-center justify-center text-slate-400">
                    <Package className="w-8 h-8" />
                  </div>
                  <Badge
                    variant={p.available_quantity > 0 ? 'success' : 'danger'}
                    className="absolute top-2 right-2 z-10"
                  >
                    {p.available_quantity > 0 ? 'Tersedia' : 'Habis'}
                  </Badge>
                </div>
                <div className="p-4">
                  <h3 className="font-bold text-slate-900 text-base line-clamp-1 mb-1">
                    {p.product_name}
                  </h3>
                  <p className="text-xs text-slate-500 truncate mb-3">
                    {p.business_name}
                  </p>
                  <div className="flex justify-between items-baseline mb-3">
                    <span className="font-bold text-rural-600 text-lg">
                      {formatRupiah(p.price)}
                    </span>
                    <span className="text-xs text-slate-500">/{p.unit}</span>
                  </div>
                  <div className="space-y-1 text-xs text-slate-600 mb-3">
                    <div className="flex gap-2">
                      <Truck className="w-3 h-3" />
                      <span>{p.available_quantity} {p.unit} tersedia</span>
                    </div>
                    <div className="flex gap-2">
                      <span>{p.city}, {p.province}</span>
                    </div>
                  </div>
                  <div className="mt-3 bg-rural-50 p-3 rounded-lg">
                    <p className="text-[11px] font-medium text-rural-700 mb-1">
                      Alasan rekomendasi:
                    </p>
                    <p className="text-xs text-rural-600">
                      Cocok dengan kebutuhan Anda dan tersedia dengan stok
                      {p.available_quantity} {p.unit}.
                    </p>
                  </div>
                </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
