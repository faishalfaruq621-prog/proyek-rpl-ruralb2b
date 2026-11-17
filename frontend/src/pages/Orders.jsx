import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { orderService } from '../api/auth'
import { Card } from '../components/ui/Card'
import { CardHeader } from '../components/ui/Card'
import { CardBody } from '../components/ui/Card'
import { CardFooter } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { formatRupiah, formatDate } from '../utils/format'
import { ArrowRight, CheckCircle } from 'lucide-react'

const STATUS_BADGE = {
  completed: 'success',
  cancelled: 'danger',
  pending: 'warning',
  confirmed: 'default',
  processing: 'default',
  shipped: 'default',
}

export default function Orders() {
  const location = useLocation()
  const searchParams = new URLSearchParams(location.search)
  const statusFilter = searchParams.get('status') || ''
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const justCreated = location.state?.created === true
  const createdCount = location.state?.count || 0

  useEffect(() => {
    loadOrders()
  }, [statusFilter])

  const loadOrders = async () => {
    setLoading(true)
    setError(null)
    try {
      // Mendukung tautan "Riwayat Transaksi" (/pesanan?status=completed):
      // backend menerima filter status pada GET /orders.
      const params = {}
      if (statusFilter) params.status = statusFilter
      const res = await orderService.getMyOrders(params)
      const data = res.data?.data || res.data || {}
      setOrders(Array.isArray(data.items) ? data.items : Array.isArray(data.orders) ? data.orders : [])
    } catch (err) {
      console.error('Gagal memuat pesanan:', err)
      setError(err.response?.data?.message || 'Gagal memuat pesanan')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rural-600"></div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {justCreated && (
        <Card className="mb-6 border-rural-200 bg-rural-50">
          <CardBody className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-rural-600 text-white flex items-center justify-center shrink-0">
              <CheckCircle className="w-6 h-6" />
            </div>
            <div>
              <h2 className="font-bold text-rural-900">Pesanan berhasil dibuat</h2>
              <p className="text-sm text-rural-700">
                {createdCount > 1
                  ? `${createdCount} pesanan dibuat karena item berasal dari beberapa penjual.`
                  : 'Pesanan Anda sudah tercatat dan menunggu diproses penjual.'}
              </p>
            </div>
          </CardBody>
        </Card>
      )}

      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="font-display font-bold text-2xl text-slate-900">
            {statusFilter === 'completed' ? 'Riwayat Transaksi' : 'Pesanan Saya'}
          </h1>
          {statusFilter === 'completed' && (
            <Link to="/pesanan" className="text-sm text-rural-600 hover:text-rural-700">
              Lihat semua status pesanan
            </Link>
          )}
        </div>
        <Link to="/katalog" className="text-sm text-rural-600 hover:text-rural-700">
          Belanja Lagi <ArrowRight className="w-3 h-3 ml-1" />
        </Link>
      </div>

      {error && (
        <Card className="p-6 mb-6 border-red-100 bg-red-50">
          <p className="text-sm text-red-700">{error}</p>
        </Card>
      )}

      {orders.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4 text-slate-400">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <h3 className="font-bold text-slate-900 mb-2">Belum ada pesanan</h3>
          <p className="text-slate-500 mb-6">Mulai belanja dari katalog produk kami.</p>
          <Button asChild>
            <Link to="/katalog">Mulai Belanja</Link>
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {orders.map((order) => {
            const status = order.order_status || 'pending'
            return (
              <Card key={order.id}>
                <CardHeader className="p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="font-bold text-slate-900">#{order.id}</h3>
                      {order.order_number && (
                        <p className="text-[11px] text-slate-400">{order.order_number}</p>
                      )}
                    </div>
                    <Badge variant={STATUS_BADGE[status] || 'default'}>{status.toUpperCase()}</Badge>
                  </div>
                  <p className="text-xs text-slate-500">{formatDate(order.created_at)}</p>
                </CardHeader>
                <CardBody className="p-4 space-y-3">
                  {order.seller?.business_name && (
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Penjual</span>
                      <span className="font-medium text-slate-900 text-right">{order.seller.business_name}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Total</span>
                    <span className="font-bold text-slate-900">{formatRupiah(order.total_amount)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Status</span>
                    <span className="font-medium text-sm capitalize">{status}</span>
                  </div>
                </CardBody>
                <CardFooter className="p-4">
                  <Button size="sm" asChild variant="outline" className="w-full">
                    <Link to={'/pesanan/' + order.id}>Lihat Detail</Link>
                  </Button>
                </CardFooter>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
