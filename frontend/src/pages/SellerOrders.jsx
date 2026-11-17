import { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { orderService } from '../api/auth'
import { Card, CardBody, CardFooter } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { formatRupiah, formatDate } from '../utils/format'
import { useToast } from '../context/ToastContext'
import { Package } from 'lucide-react'

const STATUS_BADGE = {
  completed: 'success',
  cancelled: 'danger',
  pending: 'warning',
  confirmed: 'default',
  processing: 'default',
  shipped: 'default',
}

const STATUS_TABS = [
  { value: '', label: 'Semua' },
  { value: 'pending', label: 'Pending' },
  { value: 'confirmed', label: 'Dikonfirmasi' },
  { value: 'processing', label: 'Diproses' },
  { value: 'shipped', label: 'Dikirim' },
  { value: 'completed', label: 'Selesai' },
  { value: 'cancelled', label: 'Dibatalkan' },
]

// Label aksi per status tujuan (transisi diizinkan backend melalui
// allowed_next_statuses pada setiap respons pesanan).
const ACTION_LABELS = {
  confirmed: 'Konfirmasi Pesanan',
  processing: 'Proses Pesanan',
  shipped: 'Tandai Dikirim',
  completed: 'Selesaikan Pesanan',
  cancelled: 'Batalkan',
}

export default function SellerOrders() {
  const { error: toastError, success: toastSuccess } = useToast()
  const location = useLocation()
  const navigate = useNavigate()
  const searchParams = new URLSearchParams(location.search)
  const statusFilter = searchParams.get('status') || ''

  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [updatingId, setUpdatingId] = useState(null)

  useEffect(() => {
    loadOrders()
  }, [statusFilter])

  const loadOrders = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = { page: 1, per_page: 50 }
      if (statusFilter) params.status = statusFilter
      const res = await orderService.getSellerOrders(params)
      const data = res.data?.data || res.data || {}
      setOrders(Array.isArray(data.items) ? data.items : [])
    } catch (err) {
      console.error('Gagal memuat pesanan penjual:', err)
      setError(err.response?.data?.message || 'Gagal memuat pesanan')
      setOrders([])
    } finally {
      setLoading(false)
    }
  }

  const setStatusFilter = (value) => {
    // Ulangi tetap kelola satu route dengan query status berbeda.
    navigate(value ? `/seller/pesanan?status=${value}` : '/seller/pesanan', {
      replace: true,
    })
  }

  const applyStatus = async (order, nextStatus) => {
    const msg =
      nextStatus === 'cancelled'
        ? 'Batalkan pesanan ini? Pembatalan mengembalikan stok produk.'
        : `Ubah status pesanan #${order.order_number || order.id} menjadi "${nextStatus}"?`
    if (!window.confirm(msg)) return

    setUpdatingId(order.id)
    try {
      await orderService.updateOrderStatus(order.id, { status: nextStatus, notes: '' })
      toastSuccess(`Status pesanan diperbarui menjadi ${nextStatus}.`)
      await loadOrders()
    } catch (err) {
      toastError(err.response?.data?.message || 'Gagal memperbarui status pesanan')
    } finally {
      setUpdatingId(null)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex h-screen items-center justify-center">
          <div className="flex flex-col items-center gap-2">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-rural-600"></div>
            <span className="text-sm text-slate-500">Memuat pesanan...</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="font-display font-bold text-2xl text-slate-900">
            {statusFilter === 'pending' ? 'Pesanan Masuk' : 'Riwayat Penjualan'}
          </h1>
          <p className="text-slate-600 text-sm">
            Pesanan yang diterima bisnis Anda, dengan alur pengelolaan yang diatur backend.
          </p>
        </div>
      </div>

      {/* Tab status */}
      <div className="flex flex-wrap gap-2 mb-6">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value || 'all'}
            onClick={() => setStatusFilter(tab.value)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
              statusFilter === tab.value
                ? 'bg-rural-600 text-white'
                : 'bg-white border border-slate-200 text-slate-600 hover:border-rural-400 hover:text-rural-600'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error && (
        <Card className="p-6 mb-6 border-red-100 bg-red-50">
          <p className="text-sm text-red-700">{error}</p>
        </Card>
      )}

      {orders.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4 text-slate-400">
            <Package className="w-8 h-8" />
          </div>
          <h3 className="font-bold text-slate-900 mb-2">Belum ada pesanan</h3>
          <p className="text-slate-500">
            {statusFilter
              ? `Tidak ada pesanan dengan status ${STATUS_TABS.find((t) => t.value === statusFilter)?.label.toLowerCase() || statusFilter}.`
              : 'Pesanan dari pembeli akan tampil di sini.'}
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {orders.map((order) => {
            const status = order.order_status || 'pending'
            const nextStatuses = Array.isArray(order.allowed_next_statuses)
              ? order.allowed_next_statuses
              : []
            const paymentStatus = order.payment?.payment_status
            return (
              <Card key={order.id}>
                <CardBody className="p-4 space-y-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-bold text-slate-900">#{order.order_number || order.id}</h3>
                      <p className="text-xs text-slate-500">{formatDate(order.created_at)}</p>
                    </div>
                    <Badge variant={STATUS_BADGE[status] || 'default'} className="capitalize">
                      {status}
                    </Badge>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Pembeli</span>
                    <span className="font-medium text-slate-900 text-right truncate ml-2">
                      {order.buyer?.business_name || order.buyer?.full_name || '-'}
                    </span>
                  </div>
                  {order.item_count != null && (
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Item</span>
                      <span className="font-medium text-slate-900">{order.item_count}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Total</span>
                    <span className="font-bold text-slate-900">
                      {formatRupiah(order.total_amount)}
                    </span>
                  </div>
                  {paymentStatus && paymentStatus !== 'unpaid' && (
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Pembayaran</span>
                      <span className="font-medium text-slate-900 capitalize">
                        {paymentStatus.replace(/_/g, ' ')}
                      </span>
                    </div>
                  )}
                </CardBody>
                <CardFooter className="p-4 space-y-2">
                  <Button asChild size="sm" variant="outline" className="w-full">
                    <Link to={`/seller/pesanan/${order.id}`}>Lihat Detail</Link>
                  </Button>
                  {nextStatuses.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {nextStatuses.map((s) => (
                        <Button
                          key={s}
                          size="sm"
                          variant={s === 'cancelled' ? 'secondary' : 'primary'}
                          disabled={updatingId === order.id}
                          onClick={() => applyStatus(order, s)}
                          className={`${
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
                </CardFooter>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
