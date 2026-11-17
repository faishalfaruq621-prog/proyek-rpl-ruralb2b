import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { cartService } from '../api/auth'
import { Card } from '../components/ui/Card'
import { CardHeader } from '../components/ui/Card'
import { CardBody } from '../components/ui/Card'
import { CardFooter } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { formatRupiah, PRODUCT_IMAGE_PLACEHOLDER } from '../utils/format'
import { useToast } from '../context/ToastContext'
import { Trash2, ArrowRight } from 'lucide-react'

export default function Cart() {
  const { error: toastError, success: toastSuccess } = useToast()
  const [cart, setCart] = useState({ items: [] })
  const [loading, setLoading] = useState(true)
  const [updatingId, setUpdatingId] = useState(null)
  const updatingRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    loadCart()
  }, [])

  // Backend mengirim { success, data: { cart: { items: [...] } } }.
  // Item berbentuk flat: product_id, product_name, price, unit, seller, dst.
  const applyCartResponse = (res) => {
    const body = res?.data || {}
    const cartData = body?.data?.cart || body?.cart || body?.data || {}
    setCart({
      ...cartData,
      items: Array.isArray(cartData.items) ? cartData.items : [],
    })
  }

  const loadCart = async () => {
    try {
      const res = await cartService.getCart()
      applyCartResponse(res)
    } catch (err) {
      console.error('Gagal memuat keranjang:', err)
      toastError(err.response?.data?.message || 'Gagal memuat keranjang')
      setCart({ items: [] })
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateQty = async (itemId, delta) => {
    if (updatingRef.current === itemId) return
    const item = cart.items.find((i) => i.id === itemId)
    if (!item) return

    const currentQty = Number(item.quantity) || 0
    const minimum = Number(item.minimum_order) || 1
    const newQty = Math.max(minimum, currentQty + delta)
    if (newQty === currentQty) return

    updatingRef.current = itemId
    setUpdatingId(itemId)
    try {
      const res = await cartService.updateItem(itemId, { quantity: newQty })
      applyCartResponse(res)
      toastSuccess('Jumlah produk berhasil diperbarui.')
    } catch (err) {
      toastError(err.response?.data?.message || 'Gagal mengupdate keranjang')
    } finally {
      updatingRef.current = null
      setUpdatingId(null)
    }
  }

  const handleRemove = async (itemId) => {
    if (updatingRef.current === itemId) return
    updatingRef.current = itemId
    setUpdatingId(itemId)
    try {
      const res = await cartService.deleteItem(itemId)
      applyCartResponse(res)
      toastSuccess('Produk berhasil dihapus dari keranjang.')
    } catch (err) {
      toastError(err.response?.data?.message || 'Gagal menghapus item')
    } finally {
      updatingRef.current = null
      setUpdatingId(null)
    }
  }

  const subtotal = cart.items.reduce((sum, item) => {
    const itemSubtotal = Number(item.subtotal)
    if (Number.isFinite(itemSubtotal)) return sum + itemSubtotal
    return sum + (Number(item.price) || 0) * (Number(item.quantity) || 0)
  }, 0)

  const totalQuantity = cart.items.reduce(
    (sum, item) => sum + (Number(item.quantity) || 0),
    0
  )

  const hasUnavailableItem = cart.items.some((item) => item.is_available === false)

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rural-600"></div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col lg:flex-row gap-8">
        <div className="lg:w-2/3">
          <div className="mb-6">
            <h1 className="font-display font-bold text-2xl text-slate-900">Keranjang Belanja</h1>
            <p className="text-slate-600">Periksa pesanan Anda sebelum checkout</p>
          </div>

          {cart.items.length === 0 ? (
            <Card className="p-12 text-center">
              <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4 text-slate-400">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-2 2 2 2 0 012-2z" />
                </svg>
              </div>
              <h3 className="font-bold text-slate-900 mb-2">Keranjang kosong</h3>
              <p className="text-slate-500 mb-6">Belum ada item dalam keranjang belanja Anda.</p>
              <Button asChild>
                <Link to="/katalog">Belanja Sekarang</Link>
              </Button>
            </Card>
          ) : (
            <div className="space-y-4">
              {cart.items.map((item) => {
                const unavailable = item.is_available === false
                const productName = item.product_name || 'Produk tidak tersedia'
                const sellerName = item.seller?.business_name || 'Penjual'
                const unit = item.unit || 'kg'
                const price = Number(item.price) || 0
                const imageUrl =
                  item.image_url || PRODUCT_IMAGE_PLACEHOLDER

                return (
                  <Card key={item.id}>
                    <div className="p-4 flex gap-4 items-start">
                      <div className="w-20 h-20 bg-slate-100 rounded-xl flex items-center justify-center overflow-hidden shrink-0">
                        <img
                          src={imageUrl}
                          alt={productName}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            e.target.src = PRODUCT_IMAGE_PLACEHOLDER
                          }}
                        />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-bold text-slate-900">{productName}</h3>
                        <p className="text-sm text-slate-500">{sellerName}</p>
                        <div className="mt-2 flex items-baseline gap-2">
                          <span className="font-bold text-rural-600">{formatRupiah(price)}</span>
                          <span className="text-sm text-slate-500">/{unit}</span>
                        </div>
                        {unavailable && (
                          <p className="text-xs text-red-500 mt-1">
                            {item.availability_message || 'Produk sedang tidak tersedia.'}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleUpdateQty(item.id, -1)}
                          aria-label="Kurangi jumlah"
                          disabled={updatingId === item.id}
                        >
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 12H4" />
                          </svg>
                        </Button>
                        <span className="w-8 text-center font-medium">{item.quantity}</span>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleUpdateQty(item.id, 1)}
                          aria-label="Tambah jumlah"
                          disabled={updatingId === item.id}
                        >
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                          </svg>
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleRemove(item.id)}
                          className="text-red-500 hover:bg-red-50"
                          aria-label="Hapus item"
                          disabled={updatingId === item.id}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>
          )}
        </div>
        <div className="lg:w-1/3">
          <Card>
            <CardHeader>
              <h2 className="font-bold text-lg text-slate-900">Ringkasan Pesanan</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Subtotal ({totalQuantity} item)</span>
                <span className="font-medium text-slate-900">{formatRupiah(subtotal)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Biaya pengiriman</span>
                <span className="text-slate-500">Dihitung saat checkout</span>
              </div>
              <div className="h-px bg-slate-100 my-2"></div>
              <div className="flex justify-between text-lg font-bold">
                <span className="text-slate-900">Total</span>
                <span className="text-rural-600">{formatRupiah(subtotal)}</span>
              </div>
            </CardBody>
            <CardFooter>
              {cart.items.length > 0 ? (
                <Button
                  onClick={() => navigate('/checkout')}
                  className="w-full bg-rural-600 hover:bg-rural-700 text-white"
                  disabled={hasUnavailableItem}
                >
                  {hasUnavailableItem ? 'Perbaiki Item Tidak Tersedia' : 'Lanjutkan Checkout'}
                  {!hasUnavailableItem && <ArrowRight className="w-4 h-4 ml-2" />}
                </Button>
              ) : (
                <Button variant="outline" className="w-full" asChild>
                  <Link to="/katalog">Lanjutkan Belanja</Link>
                </Button>
              )}
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  )
}
