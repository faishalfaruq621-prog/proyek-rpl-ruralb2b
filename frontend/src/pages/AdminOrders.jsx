import { useState, useEffect } from 'react'
import { adminService } from '../api/auth'
import { Card, CardBody } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { formatRupiah, formatDate } from '../utils/format'
import { ShoppingCart } from 'lucide-react'

const STATUS_BADGE = {
  completed: 'success',
  cancelled: 'danger',
  pending: 'warning',
  confirmed: 'default',
  processing: 'default',
  shipped: 'default',
}

const STATUS_FILTERS = [
  { value: '', label: 'Semua' },
  { value: 'pending', label: 'Pending' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'processing', label: 'Processing' },
  { value: 'shipped', label: 'Shipped' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
]

export default function AdminOrders() {
  const [orders, setOrders] = useState([])
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadOrders()
  }, [statusFilter])

  const loadOrders = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = { page: 1, per_page: 50, sort: 'newest' }
      if (statusFilter) params.status = statusFilter
      const res = await adminService.getOrders(params)
      const data = res.data?.data || {}
      setOrders(Array.isArray(data.items) ? data.items : [])
    } catch (err) {
      console.error('Gagal memuat transaksi:', err)
      setError(err.response?.data?.message || 'Gagal memuat transaksi')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-rural-600"></div>
          <span className="text-sm text-slate-500">Memuat transaksi...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="font-display font-bold text-2xl text-slate-900">Monitoring Transaksi</h1>
        <p className="text-slate-600 text-sm">
          Semua pesanan platform (read-only untuk admin).
        </p>
      </div>

      <div className="flex flex-wrap gap-2 mb-6">
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.value || 'all'}
            onClick={() => setStatusFilter(f.value)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
              statusFilter === f.value
                ? 'bg-rural-600 text-white'
                : 'bg-white border border-slate-200 text-slate-600 hover:border-rural-400 hover:text-rural-600'
            }`}
          >
            {f.label}
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
            <ShoppingCart className="w-8 h-8" />
          </div>
          <h3 className="font-bold text-slate-900 mb-2">Tidak ada transaksi</h3>
          <p className="text-slate-500">Belum ada pesanan dengan filter ini.</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {orders.map((order) => (
            <Card key={order.id}>
              <CardBody className="p-4 flex flex-col sm:flex-row sm:items-center gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-bold text-slate-900 text-sm">
                      #{order.order_number || order.id}
                    </p>
                    <Badge variant={STATUS_BADGE[order.order_status] || 'default'} className="capitalize text-[10px]">
                      {order.order_status}
                    </Badge>
                    <Badge
                      variant={order.payment?.payment_status === 'paid' ? 'success' : 'warning'}
                      className="text-[10px] capitalize"
                    >
                      bayar: {(order.payment?.payment_status || 'unpaid').replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Pembeli: {order.buyer?.business_name || order.buyer?.full_name || '-'} · Penjual:{' '}
                    {order.seller?.business_name || '-'} · {formatDate(order.created_at)}
                  </p>
                  <p className="text-[11px] text-slate-400">
                    {order.item_count} item · alamat: {order.shipping_address || '-'}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <p className="font-bold text-slate-900">{formatRupiah(order.total_amount)}</p>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
