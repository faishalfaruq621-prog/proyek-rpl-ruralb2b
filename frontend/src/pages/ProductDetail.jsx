import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { productService, cartService, chatService } from '../api/auth'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { formatRupiah, PRODUCT_IMAGE_PLACEHOLDER } from '../utils/format'
import { useToast } from '../context/ToastContext'
import { ShoppingCart, ArrowLeft, Mail } from 'lucide-react'

export default function ProductDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { error: toastError, success: toastSuccess } = useToast()
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)
  const [quantity, setQuantity] = useState(1)
  const [startingChat, setStartingChat] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await productService.getProduct(id)
        const data = res.data?.data?.product || res.data?.data || res.data
        setProduct(data)
        const minimum = Number(data?.minimum_order) || 1
        setQuantity(minimum)
      } catch (err) {
        console.error('Gagal memuat detail produk:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  const handleAddToCart = async () => {
    try {
      await cartService.addItem({ product_id: Number(id), quantity })
      toastSuccess('Produk berhasil ditambahkan ke keranjang.')
      navigate('/keranjang')
    } catch (err) {
      toastError(err.response?.data?.message || 'Gagal menambahkan ke keranjang')
    }
  }

  // Chat dengan penjual produk; percakapan dibuat/digunakan ulang
  // berdasarkan produk (backend mengunci pembeli = user login).
  const handleChatSeller = async () => {
    if (startingChat) return
    setStartingChat(true)
    try {
      const res = await chatService.startConversation({ product_id: Number(id) })
      const convId = res.data?.data?.conversation?.id
      navigate('/chat/' + (convId || ''))
    } catch (err) {
      toastError(err.response?.data?.message || 'Gagal membuka percakapan')
    } finally {
      setStartingChat(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-rural-600"></div>
          <span className="text-sm text-slate-500">Memuat detail produk...</span>
        </div>
      </div>
    )
  }

  if (!product) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h2 className="text-slate-900 font-bold mb-2">Produk tidak ditemukan</h2>
          <Button asChild variant="outline" onClick={() => navigate('/katalog')}>
            <ArrowLeft className="w-4 h-4 mr-2" /> Kembali ke Katalog
          </Button>
        </div>
      </div>
    )
  }

  const seller = product.business_profile || product.seller || {}
  const images = product.images || []

  return (
    <div className="min-h-screen bg-earth-50">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumb */}
        <nav className="flex gap-2 text-sm text-slate-500 mb-8">
          <Link to="/" className="hover:text-rural-600 transition-colors">
            Beranda
          </Link>
          <span className="text-slate-400">/</span>
          <Link to="/katalog" className="hover:text-rural-600 transition-colors">
            Katalog
          </Link>
          <span className="text-slate-400">/</span>
          <span className="text-slate-900 font-medium">{product.product_name}</span>
        </nav>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Gallery */}
          <div className="lg:w-1/2">
            <div className="grid grid-cols-2 gap-3 mb-4">
              {[0, 1, 2, 3].map((i) => (
                <button
                  key={i}
                  className="aspect-square rounded-2xl overflow-hidden border border-slate-200 bg-slate-100 flex items-center justify-center"
                  onClick={() => {}}
                >
                  <img
                    src={images[i]?.url || PRODUCT_IMAGE_PLACEHOLDER}
                    alt={`Foto ${i + 1}`}
                    className="w-full h-full object-cover opacity-80 hover:opacity-100 transition-opacity"
                    onError={(e) => {
                      e.target.src = PRODUCT_IMAGE_PLACEHOLDER
                    }}
                  />
                </button>
              ))}
            </div>
            <div className="h-96 bg-slate-100 rounded-2xl overflow-hidden border border-slate-100 relative">
              <img
                src={images[0]?.url || PRODUCT_IMAGE_PLACEHOLDER}
                alt={product.product_name}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.target.src = PRODUCT_IMAGE_PLACEHOLDER
                }}
              />
            </div>
          </div>

          {/* Info */}
          <div className="lg:w-1/2 space-y-6">
            <div>
              <div className="flex justify-between items-start mb-2">
                <h1 className="font-display font-bold text-2xl md:text-3xl text-slate-900 leading-tight">
                  {product.product_name}
                </h1>
                <Badge
                  variant={product.is_in_stock === false ? 'danger' : 'success'}
                  className="text-sm"
                >
                  {product.is_in_stock === false ? 'Habis' : 'Tersedia'}
                </Badge>
              </div>
              {product.category && (
                <span className="inline-block px-3 py-1 rounded-full bg-rural-50 text-rural-700 text-xs font-medium mb-4 border border-rural-100">
                  {/* Backend mengirim category sebagai objek {id, name} */}
                  {product.category?.name || ''}
                </span>
              )}
              <p className="text-slate-600 text-sm leading-relaxed mb-4">
                {product.description || '-'}
              </p>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="font-bold text-rural-600 text-3xl">
                  {formatRupiah(product.price)}
                </span>
                <span className="text-sm text-slate-500">/{product.unit || 'kg'}</span>
              </div>
              <p className="text-sm text-slate-500 mt-2">
                Minimum order: {product.minimum_order || 1} {product.unit || 'kg'}
              </p>
              <p className="text-sm text-slate-500 mt-1">
                Stok: {product.available_quantity ?? 'Tersedia'}
              </p>
            </div>

            {/* Seller info */}
            <Card className="p-5">
              <div className="flex items-start gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-rural-100 flex items-center justify-center text-rural-600 font-bold shrink-0">
                  {seller.business_name?.charAt(0) || 'P'}
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">
                    {seller.business_name || 'Penjual'}
                  </h3>
                  <p className="text-xs text-slate-500">Toko UMKM Pedesaan</p>
                </div>
              </div>
              <div className="space-y-3">
                <button
                  onClick={handleChatSeller}
                  disabled={startingChat}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-slate-50 text-slate-700 text-sm hover:bg-rural-50 hover:text-rural-600 transition-colors disabled:opacity-50"
                >
                  <Mail className="w-4 h-4" />
                  {startingChat ? 'Membuka chat...' : 'Chat Penjual'}
                </button>
              </div>
            </Card>

            {/* Quantity selector */}
            {product.is_in_stock !== false && (
              <div className="flex items-center gap-4">
                <label className="text-sm font-medium text-slate-700">Jumlah</label>
                <div className="flex items-center gap-2 border border-slate-200 rounded-xl overflow-hidden">
                  <button
                    onClick={() =>
                      setQuantity((q) =>
                        Math.max(
                          Number(product?.minimum_order) || 1,
                          q - 1
                        )
                      )
                    }
                    className="w-8 h-8 bg-slate-50 hover:bg-slate-100 text-slate-600"
                  >
                    −
                  </button>
                  <span className="w-8 text-center text-sm font-medium">{quantity}</span>
                  <button
                    onClick={() => setQuantity((q) => q + 1)}
                    className="w-8 h-8 bg-slate-50 hover:bg-slate-100 text-slate-600"
                  >
                    +
                  </button>
                </div>
              </div>
            )}

            {/* Add to cart: dinonaktifkan saat stok tersedia 0 */}
            <Button
              onClick={handleAddToCart}
              disabled={product.is_in_stock === false}
              className="w-full bg-rural-600 hover:bg-rural-700 text-white px-6 py-4 rounded-2xl font-bold flex items-center justify-center gap-2 text-lg disabled:bg-slate-300 disabled:cursor-not-allowed"
            >
              <ShoppingCart className="w-5 h-5" />
              {product.is_in_stock === false ? 'Stok Habis' : 'Masukkan ke Keranjang'}
            </Button>
          </div>
        </div>

        {/* Description detail */}
        {product.description && (
          <section className="mt-16">
            <div className="container mx-auto px-4 sm:px-6 lg:px-8">
              <h2 className="font-bold text-slate-900 mb-6">Deskripsi Produk</h2>
              <Card className="p-8">
                <p className="text-slate-600 leading-relaxed text-sm">{product.description}</p>
              </Card>
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
