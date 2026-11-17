import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { cartService, orderService } from '../api/auth'
import { Card } from '../components/ui/Card'
import { CardHeader } from '../components/ui/Card'
import { CardBody } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { formatRupiah } from '../utils/format'
import { useToast } from '../context/ToastContext'
import { ArrowRight, AlertCircle } from 'lucide-react'

export default function Checkout() {
  const { error: toastError, success: toastSuccess } = useToast()
  const navigate = useNavigate()
  const submittingRef = useRef(false)
  const [form, setForm] = useState({
    shipping_address: '',
    buyer_note: '',
    payment_method: 'transfer',
    payment_reference: '',
  })
  const [cart, setCart] = useState({ items: [] })
  const [loadingCart, setLoadingCart] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadCart()
  }, [])

  const loadCart = async () => {
    try {
      const res = await cartService.getCart()
      const data = res.data?.data?.cart || res.data?.data || {}
      setCart({
        ...data,
        items: Array.isArray(data.items) ? data.items : [],
      })
    } catch (err) {
      console.error('Gagal memuat keranjang:', err)
      toastError(err.response?.data?.message || 'Gagal memuat keranjang')
      setCart({ items: [] })
    } finally {
      setLoadingCart(false)
    }
  }

  const items = cart.items || []
  const totalQuantity = items.reduce((sum, item) => sum + (Number(item.quantity) || 0), 0)
  const subtotal = items.reduce((sum, item) => sum + (Number(item.subtotal) || 0), 0)
  const hasUnavailableItem = items.some((item) => item.is_available === false)
  const canSubmit = items.length > 0 && !hasUnavailableItem && !submitting && !loadingCart

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (submittingRef.current) return
    if (items.length === 0) {
      toastError('Keranjang kosong. Tambahkan produk terlebih dahulu.')
      return
    }
    submittingRef.current = true
    setSubmitting(true)
    try {
      const res = await orderService.checkout(form)
      const orders = res.data?.data?.orders || []
      if (orders.length === 0) {
        toastError('Checkout tidak mengembalikan data pesanan. Silakan cek daftar pesanan.')
        navigate('/pesanan', { replace: true })
        return
      }
      toastSuccess('Pesanan berhasil dibuat.')
      if (orders.length === 1) {
        navigate('/pesanan/' + orders[0].id, { state: { created: true } })
      } else {
        navigate('/pesanan', { state: { created: true, count: orders.length } })
      }
    } catch (err) {
      toastError(err.response?.data?.message || 'Checkout gagal. Silakan coba lagi.')
    } finally {
      submittingRef.current = false
      setSubmitting(false)
    }
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col lg:flex-row gap-8">
        <div className="lg:w-2/3">
          <Card>
            <CardHeader>
              <h1 className="font-display font-bold text-2xl text-slate-900">Checkout</h1>
              <p className="text-slate-600">Isi detail pengiriman dan pembayaran</p>
            </CardHeader>
            <CardBody>
              <form onSubmit={handleSubmit} className="space-y-6">
                {!loadingCart && items.length === 0 && (
                  <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-50 border border-amber-100">
                    <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-amber-800">Keranjang Anda kosong</p>
                      <p className="text-xs text-amber-700 mt-1">
                        Tambahkan produk dari katalog sebelum melakukan checkout.
                      </p>
                      <Link to="/katalog" className="text-xs font-medium text-rural-600 hover:text-rural-700 mt-2 inline-block">
                        Buka Katalog
                      </Link>
                    </div>
                  </div>
                )}

                {hasUnavailableItem && (
                  <div className="flex items-start gap-3 p-4 rounded-xl bg-red-50 border border-red-100">
                    <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                    <p className="text-sm text-red-700">
                      Ada item yang tidak tersedia. Perbaiki keranjang Anda sebelum checkout.
                    </p>
                  </div>
                )}

                {items.length > 0 && (
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                    <h2 className="font-bold text-sm text-slate-900 mb-3">
                      Ringkasan Item ({items.length} produk, {totalQuantity} item)
                    </h2>
                    <div className="space-y-2">
                      {items.map((item) => (
                        <div key={item.id} className="flex justify-between text-sm">
                          <span className="text-slate-600">
                            {item.product_name || 'Produk'} × {item.quantity}
                          </span>
                          <span className="font-medium text-slate-900">
                            {formatRupiah(item.subtotal ?? (Number(item.price) || 0) * (Number(item.quantity) || 0))}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="label">Alamat Pengiriman</label>
                    <Input
                      type="text"
                      placeholder="Jl. Raya Desa No. 1, Sukamaju, Cibiru"
                      value={form.shipping_address}
                      onChange={(e) => setForm({ ...form, shipping_address: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <label className="label">Catatan Pembeli</label>
                    <Input
                      type="text"
                      placeholder="Tolong dikirim pagi hari"
                      value={form.buyer_note}
                      onChange={(e) => setForm({ ...form, buyer_note: e.target.value })}
                    />
                  </div>
                </div>
                <div>
                  <label className="label">Metode Pembayaran</label>
                  <select
                    className="input"
                    value={form.payment_method}
                    onChange={(e) => setForm({ ...form, payment_method: e.target.value })}
                  >
                    <option value="transfer">Transfer Bank</option>
                    <option value="ewallet">Dompet Digital</option>
                    <option value="cod">Tunai saat Terima (COD)</option>
                  </select>
                </div>
                <div>
                  <label className="label">Referensi Pembayaran</label>
                  <Input
                    type="text"
                    placeholder="TRX-20261109-001"
                    value={form.payment_reference}
                    onChange={(e) => setForm({ ...form, payment_reference: e.target.value })}
                  />
                  <p className="text-xs text-slate-400 mt-1">Gunakan referensi ini saat transfer untuk memudahkan konfirmasi penjual.</p>
                </div>
                <div className="pt-4 border-t border-slate-100">
                  <div className="flex justify-between items-baseline mb-2">
                    <span className="text-slate-600 text-sm">Total yang akan dibayar</span>
                    <span className="font-bold text-rural-600 text-lg">{formatRupiah(subtotal)}</span>
                  </div>
                  <Button
                    type="submit"
                    className="w-full bg-rural-600 hover:bg-rural-700 text-white py-3"
                    disabled={!canSubmit}
                  >
                    {submitting ? 'Memproses Pesanan...' : 'Buat Pesanan'}
                    {!submitting && <ArrowRight className="w-4 h-4 ml-2" />}
                  </Button>
                </div>
              </form>
            </CardBody>
          </Card>
        </div>
        <div className="lg:w-1/3">
          <Card className="bg-rural-50 border border-rural-100">
            <CardHeader>
              <h2 className="font-bold text-lg text-rural-900">Panduan Pembayaran</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              <div className="flex gap-3">
                <div className="w-10 h-10 rounded-lg bg-white flex items-center justify-center text-rural-600 border border-rural-200">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 6l2 2M17 6l2 2M17 6l2 2M17 6l2 2M17 6l2 2M17 6l2 2M17 6l2 2" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-bold text-sm text-slate-900">Pesanan Dibuat</h3>
                  <p className="text-xs text-slate-500">Pesanan akan dibuat setelah konfirmasi checkout.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="w-10 h-10 rounded-lg bg-white flex items-center justify-center text-rural-600 border border-rural-200">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M1 12h22M2 12h1.43M20 12h1.43M6 12h1.43M18 12h1.43M3 16.29M21 16.29" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-bold text-sm text-slate-900">Transfer Bank</h3>
                  <p className="text-xs text-slate-500">Transfer ke rekening penjual dan unggah bukti pembayaran.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="w-10 h-10 rounded-lg bg-white flex items-center justify-center text-rural-600 border border-rural-200">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903M5 14h16a4 4 0 01-.88 7.903M7 16a4 4 0 01-.88-7.903M5 14h16a4 4 0 01-.88 7.903M7 16a4 4 0 01-.88-7.903M5 14h16a4 4 0 01-.88 7.903M7 16v6m0 0v6m0-6h6m0-6h6m-6 0h6" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-bold text-sm text-slate-900">Unggah Bukti</h3>
                  <p className="text-xs text-slate-500">Upload bukti transfer untuk diverifikasi penjual.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="w-10 h-10 rounded-lg bg-white flex items-center justify-center text-rural-600 border border-rural-200">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-bold text-sm text-slate-900">Konfirmasi Penjual</h3>
                  <p className="text-xs text-slate-500">Penjual mengonfirmasi pembayaran Anda.</p>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  )
}
