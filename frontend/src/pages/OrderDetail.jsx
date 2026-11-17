import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate, useLocation } from 'react-router-dom'
import { orderService, chatService } from '../api/auth'
import { Card } from '../components/ui/Card'
import { CardHeader } from '../components/ui/Card'
import { CardBody } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { formatRupiah, formatDate, PRODUCT_IMAGE_PLACEHOLDER } from '../utils/format'
import { useToast } from '../context/ToastContext'
import { ArrowRight, CheckCircle } from 'lucide-react'

export default function OrderDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const { error: toastError, success: toastSuccess } = useToast()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [submittingPayment, setSubmittingPayment] = useState(false)
  const [cancelling, setCancelling] = useState(false)
  const [receiving, setReceiving] = useState(false)
  const [startingChat, setStartingChat] = useState(false)

  const justCreated = location.state?.created === true

  useEffect(() => {
    loadOrder()
  }, [id])

  const loadOrder = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await orderService.getMyOrder(id)
      setOrder(res.data?.data?.order || res.data?.data || null)
    } catch (err) {
      console.error('Gagal memuat detail pesanan:', err)
      setError(err.response?.data?.message || 'Gagal memuat detail pesanan')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitPayment = async (e) => {
    e.preventDefault()
    if (submittingPayment) return
    const formData = new FormData(e.target)
    setSubmittingPayment(true)
    try {
      await orderService.submitPayment(id, {
        payment_method: formData.get('payment_method'),
        payment_reference: formData.get('payment_reference'),
        paid_at: formData.get('paid_at'),
      })
      toastSuccess('Informasi pembayaran berhasil dikirim.')
      await loadOrder()
    } catch (err) {
      toastError(err.response?.data?.message || 'Gagal mengirim informasi pembayaran')
    } finally {
      setSubmittingPayment(false)
    }
  }

  const handleCancel = async () => {
    if (cancelling) return
    if (!confirm('Yakin ingin membatalkan pesanan ini?')) return
    setCancelling(true)
    try {
      await orderService.cancelOrder(id, { reason: 'Dibatalkan oleh pembeli' })
      toastSuccess('Pesanan berhasil dibatalkan.')
      navigate('/pesanan')
    } catch (err) {
      toastError(err.response?.data?.message || 'Gagal membatalkan pesanan')
    } finally {
      setCancelling(false)
    }
  }

  // Konfirmasi penerimaan barang: shipped -> completed (backend memvalidasi).
  const handleReceive = async () => {
    if (receiving) return
    if (!confirm('Konfirmasi bahwa barang pesanan ini sudah diterima?')) return
    setReceiving(true)
    try {
      await orderService.receiveOrder(id)
      toastSuccess('Pesanan dikonfirmasi diterima.')
      await loadOrder()
    } catch (err) {
      toastError(err.response?.data?.message || 'Gagal mengonfirmasi penerimaan')
    } finally {
      setReceiving(false)
    }
  }

  // Chat dengan penjual; percakapan dibuat/reused berdasarkan pesanan.
  const handleStartChat = async () => {
    if (startingChat) return
    setStartingChat(true)
    try {
      const res = await chatService.startConversation({ order_id: Number(id) })
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rural-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center max-w-md px-4">
          <h2 className="text-slate-900 font-bold mb-2">Gagal memuat pesanan</h2>
          <p className="text-slate-500 mb-6">{error}</p>
          <Button asChild>
            <Link to="/pesanan">Kembali ke Daftar Pesanan</Link>
          </Button>
        </div>
      </div>
    )
  }

  if (!order) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <h2 className="text-slate-900 font-bold mb-2">Pesanan tidak ditemukan</h2>
          <Button asChild>
            <Link to="/pesanan">Kembali ke Daftar Pesanan</Link>
          </Button>
        </div>
      </div>
    )
  }

  const orderStatus = order.order_status || 'pending'
  const payments = Array.isArray(order.payments) ? order.payments : []
  const payment = payments.length > 0 ? payments[payments.length - 1] : order.payment || null
  const items = Array.isArray(order.items) ? order.items : []
  const sellerName = order.seller?.business_name || 'Penjual'
  const totalQuantity = items.reduce((sum, item) => sum + (Number(item.quantity) || 0), 0)

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {justCreated && (
        <Card className="mb-6 border-rural-200 bg-rural-50">
          <CardBody className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-rural-600 text-white flex items-center justify-center shrink-0">
              <CheckCircle className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h2 className="font-bold text-rural-900">Pesanan berhasil dibuat</h2>
              <p className="text-sm text-rural-700">
                Nomor pesanan{' '}
                <span className="font-semibold">{order.order_number || '#' + order.id}</span>{' '}
                — status {orderStatus}. Penjual {sellerName} akan memproses pesanan Anda.
              </p>
            </div>
            <Button asChild variant="outline" size="sm">
              <Link to="/pesanan">Lihat Semua Pesanan</Link>
            </Button>
          </CardBody>
        </Card>
      )}

      <div className="flex flex-wrap gap-2 justify-between items-center mb-6">
        <Link to="/pesanan" className="text-sm text-rural-600 hover:text-rural-700 flex items-center gap-2">
          <ArrowRight className="w-3 h-3" style={{ transform: 'rotate(180deg)' }} /> Kembali
        </Link>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onClick={handleStartChat} disabled={startingChat}>
            {startingChat ? 'Membuka...' : 'Hubungi Penjual'}
          </Button>
          {order.can_receive && (
            <Button size="sm" onClick={handleReceive} disabled={receiving} className="bg-rural-600 hover:bg-rural-700 text-white">
              {receiving ? 'Memproses...' : 'Konfirmasi Penerimaan'}
            </Button>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={handleCancel}
            disabled={orderStatus !== 'pending' || cancelling}
          >
            {cancelling ? 'Membatalkan...' : 'Batalkan Pesanan'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h1 className="font-display font-bold text-xl text-slate-900">Pesanan #{order.id}</h1>
                  {order.order_number && (
                    <p className="text-xs text-slate-500 mt-1">{order.order_number}</p>
                  )}
                </div>
                <Badge variant={orderStatus === 'completed' ? 'success' : 'default'}>
                  {orderStatus.toUpperCase()}
                </Badge>
              </div>
              <p className="text-sm text-slate-500">{formatDate(order.created_at)}</p>
            </CardHeader>
            <CardBody className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-3 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-500 uppercase">Total Pesanan</p>
                  <p className="font-bold text-slate-900">{formatRupiah(order.total_amount)}</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-500 uppercase">Status</p>
                  <p className="font-medium text-slate-700 capitalize">{orderStatus}</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-500 uppercase">Penjual</p>
                  <p className="font-medium text-slate-700">{sellerName}</p>
                </div>
              </div>
              <h3 className="font-bold text-slate-900 mb-2">
                Item Pesanan {totalQuantity > 0 ? `(${totalQuantity} item)` : ''}
              </h3>
              <div className="space-y-3">
                {items.length === 0 && (
                  <p className="text-sm text-slate-500">Tidak ada item pada pesanan ini.</p>
                )}
                {items.map((item) => (
                  <div key={item.id} className="flex gap-3 items-center p-3 bg-white border border-slate-100 rounded-xl">
                    <div className="w-12 h-12 bg-slate-100 rounded flex items-center justify-center shrink-0 overflow-hidden">
                      <img
                        src={PRODUCT_IMAGE_PLACEHOLDER}
                        alt={item.product_name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.src = PRODUCT_IMAGE_PLACEHOLDER
                        }}
                      />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-bold text-slate-900 text-sm">{item.product_name}</h4>
                      <p className="text-xs text-slate-500">{item.quantity} {item.unit || 'kg'}</p>
                    </div>
                    <span className="font-medium text-slate-900">
                      {formatRupiah(item.subtotal ?? (item.price || 0) * (item.quantity || 0))}
                    </span>
                  </div>
                ))}
              </div>
              {order.shipping_address && (
                <div className="pt-4 border-t border-slate-100">
                  <p className="text-xs text-slate-500 uppercase mb-1">Alamat Pengiriman</p>
                  <p className="text-sm text-slate-700">{order.shipping_address}</p>
                </div>
              )}
              {order.buyer_note && (
                <div className="pt-4 border-t border-slate-100">
                  <p className="text-xs text-slate-500 uppercase mb-1">Catatan Pembeli</p>
                  <p className="text-sm text-slate-700">{order.buyer_note}</p>
                </div>
              )}
            </CardBody>
          </Card>

          {payment && (
            <Card>
              <CardHeader>
                <h2 className="font-bold text-lg text-slate-900">Informasi Pembayaran</h2>
              </CardHeader>
              <CardBody className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="p-3 bg-slate-50 rounded-xl">
                    <p className="text-xs text-slate-500 uppercase">Status Pembayaran</p>
                    <Badge
                      variant={payment.payment_status === 'paid' ? 'success' : 'warning'}
                      className="text-xs"
                    >
                      {(payment.payment_status || 'unpaid').toUpperCase()}
                    </Badge>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl">
                    <p className="text-xs text-slate-500 uppercase">Nominal</p>
                    <p className="font-bold text-slate-900">{formatRupiah(payment.amount)}</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl">
                    <p className="text-xs text-slate-500 uppercase">Metode</p>
                    <p className="text-sm text-slate-700">{payment.payment_method || '-'}</p>
                  </div>
                  {payment.payment_reference && (
                    <div className="p-3 bg-slate-50 rounded-xl">
                      <p className="text-xs text-slate-500 uppercase">Referensi</p>
                      <p className="text-sm text-slate-700">{payment.payment_reference}</p>
                    </div>
                  )}
                </div>

                {payment.payment_status === 'unpaid' && (
                  <div className="pt-4 border-t border-slate-100">
                    <form onSubmit={handleSubmitPayment} className="space-y-4">
                      <h3 className="font-bold text-sm text-slate-900 mb-3">Kirim Informasi Pembayaran</h3>
                      <div className="space-y-3">
                        <div>
                          <label className="label">Metode Pembayaran</label>
                          <select
                            name="payment_method"
                            className="input"
                            defaultValue={payment.payment_method || 'transfer'}
                            required
                          >
                            <option value="transfer">Transfer Bank</option>
                            <option value="ewallet">Dompet Digital</option>
                            <option value="cod">Tunai saat Terima</option>
                          </select>
                        </div>
                        <div>
                          <label className="label">Referensi Pembayaran</label>
                          <Input
                            name="payment_reference"
                            placeholder="TRX-20261109-001"
                            defaultValue={payment.payment_reference || ''}
                            required
                          />
                        </div>
                        <div>
                          <label className="label">Tanggal Pembayaran</label>
                          <Input type="datetime-local" name="paid_at" required />
                        </div>
                      </div>
                      <Button
                        type="submit"
                        className="w-full bg-rural-600 hover:bg-rural-700 text-white py-2"
                        disabled={submittingPayment}
                      >
                        {submittingPayment ? 'Mengirim...' : 'Kirim Informasi Pembayaran'}
                      </Button>
                    </form>
                  </div>
                )}

                {payment.payment_status === 'pending_confirmation' && (
                  <div className="pt-4 border-t border-slate-100 bg-amber-50 rounded-xl p-4">
                    <h3 className="font-bold text-sm text-amber-800 mb-2">Tunggu Konfirmasi Penjual</h3>
                    <p className="text-xs text-amber-700">
                      Pembayaran Anda telah dikirim dan menunggu konfirmasi dari penjual.
                    </p>
                  </div>
                )}

                {payment.payment_status === 'paid' && (
                  <div className="pt-4 border-t border-slate-100 bg-rural-50 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="w-4 h-4 text-rural-600" />
                      <h3 className="font-bold text-sm text-rural-700">Pembayaran Dikonfirmasi</h3>
                    </div>
                    <p className="text-xs text-rural-700">
                      Pembayaran Anda telah dikonfirmasi oleh penjual. Pesanan akan segera diproses.
                    </p>
                  </div>
                )}
              </CardBody>
            </Card>
          )}

          {!payment && (
            <Card>
              <CardHeader>
                <h2 className="font-bold text-lg text-slate-900">Belum Ada Informasi Pembayaran</h2>
              </CardHeader>
              <CardBody className="space-y-4">
                <p className="text-sm text-slate-600">
                  Silakan kirim informasi pembayaran untuk memproses pesanan ini.
                </p>
                <form onSubmit={handleSubmitPayment} className="space-y-4">
                  <div className="space-y-3">
                    <div>
                      <label className="label">Metode Pembayaran</label>
                      <select name="payment_method" className="input" defaultValue="transfer" required>
                        <option value="transfer">Transfer Bank</option>
                        <option value="ewallet">Dompet Digital</option>
                        <option value="cod">Tunai saat Terima</option>
                      </select>
                    </div>
                    <div>
                      <label className="label">Referensi Pembayaran</label>
                      <Input name="payment_reference" placeholder="TRX-20261109-001" required />
                    </div>
                    <div>
                      <label className="label">Tanggal Pembayaran</label>
                      <Input type="datetime-local" name="paid_at" required />
                    </div>
                  </div>
                  <Button
                    type="submit"
                    className="w-full bg-rural-600 hover:bg-rural-700 text-white py-2"
                    disabled={submittingPayment}
                  >
                    {submittingPayment ? 'Mengirim...' : 'Kirim Informasi Pembayaran'}
                  </Button>
                </form>
              </CardBody>
            </Card>
          )}
        </div>

        <div className="lg:col-span-1">
          <Card className="bg-rural-50 border border-rural-100">
            <CardHeader>
              <h2 className="font-bold text-lg text-rural-900">Alur Pesanan</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-rural-600 text-white flex items-center justify-center text-xs font-bold">
                  1
                </div>
                <div className="flex-1">
                  <p className="font-bold text-sm text-slate-900">Pesanan Dibuat</p>
                  <p className="text-xs text-slate-500">Pesanan Anda telah dibuat dan menunggu pembayaran.</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-rural-600 text-white flex items-center justify-center text-xs font-bold">
                  2
                </div>
                <div className="flex-1">
                  <p className="font-bold text-sm text-slate-900">Pembayaran</p>
                  <p className="text-xs text-slate-500">Kirim informasi pembayaran dan bukti transfer.</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-500 flex items-center justify-center text-xs font-bold">
                  3
                </div>
                <div className="flex-1">
                  <p className="font-bold text-sm text-slate-900">Konfirmasi Penjual</p>
                  <p className="text-xs text-slate-500">Penjual mengonfirmasi pembayaran Anda.</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-500 flex items-center justify-center text-xs font-bold">
                  4
                </div>
                <div className="flex-1">
                  <p className="font-bold text-sm text-slate-900">Pengiriman</p>
                  <p className="text-xs text-slate-500">Barang akan dikirim ke alamat Anda.</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-500 flex items-center justify-center text-xs font-bold">
                  5
                </div>
                <div className="flex-1">
                  <p className="font-bold text-sm text-slate-900">Selesai</p>
                  <p className="text-xs text-slate-500">Pesanan telah selesai.</p>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  )
}
