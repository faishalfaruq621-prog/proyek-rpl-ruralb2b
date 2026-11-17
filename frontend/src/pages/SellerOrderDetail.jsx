import { useState, useEffect } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { orderService, chatService } from '../api/auth'
import { Card, CardBody } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { formatRupiah, formatDate } from '../utils/format'
import { useToast } from '../context/ToastContext'
import { ArrowLeft, Mail } from 'lucide-react'

const STATUS_BADGE = {
  completed: 'success',
  cancelled: 'danger',
  pending: 'warning',
  confirmed: 'default',
  processing: 'default',
  shipped: 'default',
}

const ACTION_LABELS = {
  confirmed: 'Konfirmasi Pesanan',
  processing: 'Proses Pesanan',
  shipped: 'Tandai Dikirim',
  completed: 'Selesaikan Pesanan',
  cancelled: 'Batalkan Pesanan',
}

export default function SellerOrderDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { error: toastError, success: toastSuccess } = useToast()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)
  const [startingChat, setStartingChat] = useState(false)

  useEffect(() => {
    loadOrder()
  }, [id])

  // Chat dengan pembeli; percakapan pesanan diambil/dibuat via backend.
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

  const loadOrder = async () => {
    setLoading(true)
    try {
      const res = await orderService.getSellerOrder(id)
      setOrder(res.data?.data?.order || res.data?.order || null)
    } catch (err) {
      console.error('Gagal memuat detail pesanan:', err)
      setOrder(null)
      if (err.response?.status !== 404) {
        toastError(err.response?.data?.message || 'Gagal memuat detail pesanan')
      }
    } finally {
      setLoading(false)
    }
  }

  const applyStatus = async (nextStatus) => {
    const msg =
      nextStatus === 'cancelled'
        ? 'Batalkan pesanan ini? Pembatalan mengembalikan stok produk.'
        : `Ubah status pesanan menjadi "${nextStatus}"?`
    if (!window.confirm(msg)) return

    setUpdating(true)
    try {
      await orderService.updateOrderStatus(id, { status: nextStatus, notes: '' })
      toastSuccess(`Status pesanan diperbarui menjadi ${nextStatus}.`)
      await loadOrder()
    } catch (err) {
      toastError(err.response?.data?.message || 'Gagal memperbarui status pesanan')
    } finally {
      setUpdating(false)
    }
  }

  const confirmPayment = async () => {
    if (!window.confirm('Konfirmasi pembayaran pesanan ini?')) return
    setUpdating(true)
    try {
      await orderService.confirmPayment(id, {})
      toastSuccess('Pembayaran berhasil dikonfirmasi.')
      await loadOrder()
    } catch (err) {
      toastError(err.response?.data?.message || 'Gagal mengonfirmasi pembayaran')
    } finally {
      setUpdating(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-rural-600"></div>
          <span className="text-sm text-slate-500">Memuat detail pesanan...</span>
        </div>
      </div>
    )
  }

  if (!order) {
    return (
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-16">
          <h2 className="font-bold text-slate-900 mb-2">Pesanan tidak ditemukan</h2>
          <p className="text-slate-500 mb-6 text-sm">
            Pesanan tidak ada atau bukan milik bisnis Anda.
          </p>
          <Button asChild variant="outline">
            <Link to="/seller/pesanan">
              <ArrowLeft className="w-4 h-4 mr-2" /> Kembali ke Riwayat Penjualan
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  const status = order.order_status || 'pending'
  const nextStatuses = Array.isArray(order.allowed_next_statuses)
    ? order.allowed_next_statuses
    : []
  const payment = order.payment
  const logs = Array.isArray(order.status_logs) ? order.status_logs : []

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-start mb-6 gap-3">
        <div>
          <Button asChild variant="outline" size="sm" className="mb-3">
            <Link to="/seller/pesanan">
              <ArrowLeft className="w-4 h-4" /> Riwayat Penjualan
            </Link>
          </Button>
          <h1 className="font-display font-bold text-2xl text-slate-900">
            Pesanan #{order.order_number || order.id}
          </h1>
          <p className="text-sm text-slate-500">{formatDate(order.created_at)}</p>
        </div>
        <Badge variant={STATUS_BADGE[status] || 'default'} className="capitalize h-fit">
          {status}
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Kolom utama: item + pembayaran */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardBody className="p-5">
              <h2 className="font-bold text-slate-900 mb-4">Daftar Item</h2>
              <div className="divide-y divide-slate-100">
                {(order.items || []).map((item) => (
                  <div key={item.id} className="flex justify-between items-center py-3">
                    <div className="min-w-0">
                      <p className="font-medium text-slate-900 text-sm truncate">
                        {item.product_name}
                      </p>
                      <p className="text-xs text-slate-500">
                        {item.quantity} × {formatRupiah(item.price_snapshot)} / {item.unit || 'kg'}
                      </p>
                    </div>
                    <p className="font-bold text-slate-900 text-sm shrink-0 ml-4">
                      {formatRupiah(item.subtotal)}
                    </p>
                  </div>
                ))}
              </div>
              <div className="flex justify-between items-center mt-4 pt-4 border-t border-slate-200">
                <span className="font-bold text-slate-900">Total</span>
                <span className="font-bold text-lg text-rural-600">
                  {formatRupiah(order.total_amount)}
                </span>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardBody className="p-5">
              <h2 className="font-bold text-slate-900 mb-4">Pembayaran</h2>
              {payment ? (
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Metode</span>
                    <span className="font-medium text-slate-900">
                      {payment.payment_method || '-'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Status</span>
                    <span className="font-medium text-slate-900 capitalize">
                      {payment.payment_status?.replace(/_/g, ' ') || '-'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Nominal</span>
                    <span className="font-medium text-slate-900">
                      {payment.amount != null ? formatRupiah(payment.amount) : '-'}
                    </span>
                  </div>
                  {payment.payment_reference && (
                    <div className="flex justify-between">
                      <span className="text-slate-600">Referensi</span>
                      <span className="font-medium text-slate-900">{payment.payment_reference}</span>
                    </div>
                  )}
                  {payment.payment_status === 'pending_confirmation' && (
                    <Button
                      onClick={confirmPayment}
                      disabled={updating}
                      className="mt-3 w-full bg-rural-600 hover:bg-rural-700 text-white"
                    >
                      Konfirmasi Pembayaran
                    </Button>
                  )}
                </div>
              ) : (
                <p className="text-sm text-slate-500">Belum ada data pembayaran.</p>
              )}
            </CardBody>
          </Card>

          {/* Timeline status */}
          <Card>
            <CardBody className="p-5">
              <h2 className="font-bold text-slate-900 mb-4">Riwayat Status</h2>
              {logs.length === 0 ? (
                <p className="text-sm text-slate-500">Belum ada riwayat perubahan status.</p>
              ) : (
                <ol className="space-y-4">
                  {logs.map((log) => (
                    <li key={log.id} className="flex gap-3">
                      <div className="mt-1 w-2 h-2 rounded-full bg-rural-500 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-900 capitalize">
                          {(log.old_status || '—') + ' → ' + (log.new_status || log.status || '')}
                        </p>
                        {log.notes && (
                          <p className="text-xs text-slate-500">{log.notes}</p>
                        )}
                        <p className="text-[11px] text-slate-400">
                          {formatDate(log.created_at)}
                          {log.changed_by_name ? ` · ${log.changed_by_name}` : ''}
                        </p>
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </CardBody>
          </Card>
        </div>

        {/* Kolom samping: info pembeli + aksi */}
        <div className="space-y-6">
          <Card>
            <CardBody className="p-5">
              <h2 className="font-bold text-slate-900 mb-4">Informasi Pembeli</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between gap-3">
                  <span className="text-slate-600 shrink-0">Nama</span>
                  <span className="font-medium text-slate-900 text-right">
                    {order.buyer?.full_name || '-'}
                  </span>
                </div>
                <div className="flex justify-between gap-3">
                  <span className="text-slate-600 shrink-0">Bisnis</span>
                  <span className="font-medium text-slate-900 text-right">
                    {order.buyer?.business_name || '-'}
                  </span>
                </div>
              </div>
              {/* Chat dengan pembeli; percakapan dibuat/digunakan ulang
                  berdasarkan pesanan (backend memvalidasi penjual). */}
              <button
                onClick={handleStartChat}
                disabled={startingChat}
                className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-slate-50 text-slate-700 text-sm hover:bg-rural-50 hover:text-rural-600 transition-colors disabled:opacity-50"
              >
                <Mail className="w-4 h-4" />
                {startingChat ? 'Membuka chat...' : 'Hubungi Pembeli'}
              </button>
            </CardBody>
          </Card>

          <Card>
            <CardBody className="p-5">
              <h2 className="font-bold text-slate-900 mb-4">Alamat Pengiriman</h2>
              <p className="text-sm text-slate-700 whitespace-pre-wrap">
                {order.shipping_address || '-'}
              </p>
              {order.buyer_note && (
                <>
                  <h3 className="text-xs font-semibold uppercase text-slate-400 mt-4 mb-1">
                    Catatan Pembeli
                  </h3>
                  <p className="text-sm text-slate-700 whitespace-pre-wrap">{order.buyer_note}</p>
                </>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardBody className="p-5">
              <h2 className="font-bold text-slate-900 mb-4">Aksi Status</h2>
              {nextStatuses.length === 0 ? (
                <p className="text-sm text-slate-500">
                  Tidak ada aksi yang tersedia pada status ini.
                </p>
              ) : (
                <div className="space-y-2">
                  {nextStatuses.map((s) => (
                    <Button
                      key={s}
                      variant={s === 'cancelled' ? 'secondary' : 'primary'}
                      disabled={updating}
                      onClick={() => applyStatus(s)}
                      className={`w-full ${
                        s === 'cancelled'
                          ? 'border border-slate-300 text-slate-700'
                          : 'bg-rural-600 hover:bg-rural-700 text-white'
                      }`}
                    >
                      {ACTION_LABELS[s] || s}
                    </Button>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  )
}
