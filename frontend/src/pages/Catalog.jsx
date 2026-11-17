import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { productService } from '../api/auth'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { formatRupiah, PRODUCT_IMAGE_PLACEHOLDER } from '../utils/format'
import { useToast } from '../context/ToastContext'
import { getCapabilities } from '../utils/capabilities'
import { useAuth } from '../context/AuthContext'
import { Search, SortAsc } from 'lucide-react'

const SORT_OPTIONS = [
  { value: 'newest', label: 'Terbaru' },
  { value: 'oldest', label: 'Terlama' },
  { value: 'price_asc', label: 'Harga Termurah' },
  { value: 'price_desc', label: 'Harga Termahal' },
]

export default function Catalog() {
  const { error: toastError } = useToast()
  const { user } = useAuth()
  const caps = getCapabilities(user)
  const { search: locationSearch } = useLocation()
  const searchParams = new URLSearchParams(locationSearch)
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [categoryId, setCategoryId] = useState(
    searchParams.get('category_id') || ''
  )
  // Tampilkan tombol Tambah Produk hanya untuk pengguna dengan kemampuan jual,
  // jangan merender elemen yang langsung gagal akses.
  const canSell = user ? caps.canSell : false
  const [sort, setSort] = useState(searchParams.get('sort') || 'newest')

  useEffect(() => {
    let mounted = true
    const loadCategories = async () => {
      try {
        const res = await productService.getCategories()
        const data = res.data?.data || {}
        if (mounted) setCategories(Array.isArray(data.items) ? data.items : [])
      } catch (err) {
        // Katalog tetap berfungsi tanpa filter kategori.
        console.error('Gagal memuat kategori:', err)
      }
    }
    loadCategories()
    return () => {
      mounted = false
    }
  }, [])

  const fetchProducts = async () => {
    try {
      setLoading(true)
      const params = {}
      if (search) params.search = search
      // Endpoint publik memfilter berdasarkan category_id (angka), bukan
      // nama kategori teks.
      if (categoryId) params.category_id = categoryId
      if (sort) params.sort = sort
      const res = await productService.getProducts(params)
      const data = res.data?.data || res.data || {}
      const items = Array.isArray(data.items) ? data.items : (Array.isArray(data) ? data : [])
      setProducts(items)
    } catch (err) {
      toastError(err.response?.data?.message || 'Gagal memuat produk')
      setProducts([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProducts()
  }, [search, categoryId, sort])

  return (
    <div className="animate-fade-in min-h-screen bg-earth-50">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex flex-col lg:flex-row gap-6 mb-8 items-end">
          <div className="flex-1">
            <h1 className="font-display font-bold text-2xl md:text-3xl text-slate-900 mb-1">
              Katalog Produk
            </h1>
            <p className="text-slate-600">
              Temukan hasil terbaik dari mitra UMKM pedesaan kami
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
            {/* Search */}
            <div className="relative flex-1 sm:w-80">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="Cari produk..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            {/* Category filter: pilihan diambil dari GET /products/categories */}
            <div className="relative">
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="bg-white border border-slate-200 text-slate-700 text-sm rounded-xl px-3 py-2 focus:ring-2 focus:ring-rural-500 outline-none cursor-pointer w-full sm:w-auto"
              >
                <option value="">Semua Kategori</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>
            {/* Sort */}
            <div className="relative">
              <select
                value={sort}
                onChange={(e) => {
                  setSort(e.target.value)
                }}
                className="bg-white border border-slate-200 text-slate-700 text-sm rounded-xl px-3 py-2 focus:ring-2 focus:ring-rural-500 outline-none cursor-pointer"
              >
                {SORT_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
              <SortAsc className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4 pointer-events-none" />
            </div>
            {canSell && (
              <Button asChild>
                <Link to="/produk/tambah">Tambah Produk</Link>
              </Button>
            )}
          </div>
        </div>

        {/* Loading */}
        {loading ? (
          <div className="flex justify-center py-20">
            <div className="flex flex-col items-center gap-2">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-rural-600"></div>
              <span className="text-sm text-slate-500">Memuat produk...</span>
            </div>
          </div>
        ) : (
          <div>
            {/* Empty state */}
            {products.length === 0 && (
              <div className="text-center py-20">
                <div className="w-16 h-16 rounded-full bg-rural-100 flex items-center justify-center text-rural-600 mx-auto mb-4">
                  <Search className="w-6 h-6" />
                </div>
                <h3 className="font-bold text-slate-900 mb-2">Produk tidak ditemukan</h3>
                <p className="text-slate-500 mb-6">Coba ubah kata kunci pencarian atau filter Anda.</p>
                <Button asChild>
                  <Link to="/katalog">Reset Filter</Link>
                </Button>
              </div>
            )}

            {/* Product list */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {products.map((product) => {
                const inStock = product.is_in_stock !== false
                const sellerName =
                  product.seller?.business_name ||
                  product.business_profile?.business_name ||
                  'Penjual'
                return (
                  <Card
                    key={product.id}
                    className="group hover:border-rural-200 transition-border"
                  >
                    <div className="h-48 bg-slate-100 overflow-hidden mb-4 relative">
                      <img
                        src={product.images?.[0]?.url || PRODUCT_IMAGE_PLACEHOLDER}
                        alt={product.product_name}
                        className="w-full h-full object-cover opacity-90 group-hover:opacity-100"
                        onError={(e) => {
                          e.target.src = PRODUCT_IMAGE_PLACEHOLDER
                        }}
                      />
                      {/* Badge mengikuti data stok aktual, bukan selalu "Tersedia" */}
                      <Badge
                        variant={inStock ? 'success' : 'danger'}
                        className="absolute top-3 right-3 z-10"
                      >
                        {inStock ? 'Tersedia' : 'Habis'}
                      </Badge>
                    </div>
                    <div className="p-4">
                      <div className="flex justify-between items-start mb-1">
                        <h3 className="font-bold text-slate-900 text-lg line-clamp-1">{product.product_name}</h3>
                      </div>
                      <p className="text-sm text-slate-500 truncate mb-3">
                        {sellerName}
                      </p>
                      <div className="flex items-baseline gap-2 mb-4">
                        <span className="font-bold text-rural-600 text-xl">
                          {formatRupiah(product.price)}
                        </span>
                        <span className="text-sm text-slate-500">/{product.unit || 'kg'}</span>
                      </div>
                      <div className="mt-4">
                        <Button asChild size="sm" className="w-full" variant="outline">
                          <Link to={`/produk/${product.id}`}>Lihat Detail</Link>
                        </Button>
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
