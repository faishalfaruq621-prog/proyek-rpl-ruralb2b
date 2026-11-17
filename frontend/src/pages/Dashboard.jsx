import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardHeader, CardBody, CardFooter } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { formatRupiah, formatDate, PRODUCT_IMAGE_PLACEHOLDER } from '../utils/format'
import { useAuth } from '../context/AuthContext'
import { getCapabilities } from '../utils/capabilities'
import { orderService, productService } from '../api/auth'
import {
  User,
  ShoppingCart,
  Package,
  Truck,
  CheckCircle,
  Clock,
  Plus,
} from 'lucide-react'

const PAGE_SIZE = 5

const STATUS_BADGE = {
  completed: 'success',
  cancelled: 'danger',
  pending: 'warning',
  confirmed: 'default',
  processing: 'default',
  shipped: 'default',
}

function StatCard({ label, value, icon, tone }) {
  const tones = {
    blue: 'bg-blue-100 text-blue-600',
    amber: 'bg-amber-100 text-amber-600',
    rural: 'bg-rural-100 text-rural-600',
    slate: 'bg-slate-100 text-slate-600',
  }
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-slate-500 uppercase">{label}</p>
          <p className="font-bold text-2xl text-slate-900">{value}</p>
        </div>
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${tones[tone] || tones.slate}`}>
          {icon}
        </div>
      </div>
    </Card>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const caps = getCapabilities(user)
  const isAdmin = user?.role === 'admin'

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [buyer, setBuyer] = useState(null)
  const [seller, setSeller] = useState(null)

  useEffect(() => {
    loadDashboard()
  }, [user?.id])

  const loadDashboard = async () => {
    setLoading(true)
    setError(null)

    const jobs = []

    // ===== Bagian Buyer: hanya dimuat bila pengguna punya kemampuan beli =====
    if (caps.canBuy) {
      jobs.push(
        (async () => {
          const base = { page: 1, per_page: PAGE_SIZE }
          // Tiga query ringan; angka diambil dari pagination.total (jumlah
          // aktual di database, bukan dari lima item pertama).
          const [allRes, pendingRes, doneRes] = await Promise.all([
            orderService.getMyOrders(base),
            orderService.getMyOrders({ ...base, status: 'pending' }),
            orderService.getMyOrders({ ...base, status: 'completed' }),
          ])
          const asData = (res) => res.data?.data || res.data || {}
          const all = asData(allRes)
          const items = Array.isArray(all.items) ? all.items : []
          setBuyer({
            total: all.pagination?.total ?? items.length,
            pending:
              asData(pendingRes).pagination?.total ??
              (Array.isArray(asData(pendingRes).items)
                ? asData(pendingRes).items.length
                : 0),
            completed:
              asData(doneRes).pagination?.total ??
              (Array.isArray(asData(doneRes).items)
                ? asData(doneRes).items.length
                : 0),
            recent: items,
          })
        })().catch((err) => {
          console.error('Gagal memuat data pembelian:', err)
          setBuyer({ error: true })
        })
      )
    }

    // ===== Bagian Seller: hanya dimuat bila punya profil bisnis =====
    if (caps.canSell) {
      jobs.push(
        (async () => {
          const base = { page: 1, per_page: PAGE_SIZE }
          const [ordersRes, pendingRes, productsRes] = await Promise.all([
            orderService.getSellerOrders(base),
            orderService.getSellerOrders({ ...base, status: 'pending' }),
            productService.getMyProducts(base),
          ])
          const asData = (res) => res.data?.data || res.data || {}
          const orders = asData(ordersRes)
          const orderItems = Array.isArray(orders.items) ? orders.items : []
          const products = asData(productsRes)
          const productItems = Array.isArray(products.items) ? products.items : []
          setSeller({
            totalOrders: orders.pagination?.total ?? orderItems.length,
            pendingOrders:
              asData(pendingRes).pagination?.total ??
              (Array.isArray(asData(pendingRes).items)
                ? asData(pendingRes).items.length
                : 0),
            totalProducts: products.pagination?.total ?? productItems.length,
            recentOrders: orderItems,
            products: productItems,
          })
        })().catch((err) => {
          console.error('Gagal memuat data penjualan:', err)
          setSeller({ error: true })
        })
      )
    }

    try {
      await Promise.all(jobs)
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

  if (isAdmin) {
    return (
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="font-display font-bold text-2xl text-slate-900">Dashboard Admin</h1>
          <p className="text-slate-600">Kelola verifikasi UMKM dan pantau platform RuralB2B.</p>
          <div className="mt-6 flex gap-3">
            <Button asChild size="sm" className="bg-rural-600 hover:bg-rural-700 text-white">
              <Link to="/verifikasi/admin">Kelola Verifikasi</Link>
            </Button>
          </div>
        </div>
      </div>
    )
  }

  const hasBuyer = caps.canBuy && buyer && !buyer.error
  const hasSeller = caps.canSell && seller && !seller.error

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* ===== Header ===== */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center mb-8 gap-4">
        <div>
          <h1 className="font-display font-bold text-2xl text-slate-900">
            Selamat datang, {user?.full_name?.split(' ')[0] || 'Pengguna'}
          </h1>
          <p className="text-slate-600">
            {hasBuyer && hasSeller
              ? 'Ringkasan aktivitas pembelian dan penjualan bisnis Anda'
              : hasSeller
                ? 'Kelola bisnis dan pesanan Anda di sini'
                : 'Lihat pesanan dan aktivitas belanja Anda di sini'}
          </p>
        </div>
        {hasSeller && (
          <Button asChild className="bg-rural-600 hover:bg-rural-700 text-white">
            <Link to="/produk/tambah" className="flex items-center gap-1">
              <Plus className="w-4 h-4" /> Tambah Produk
            </Link>
          </Button>
        )}
      </div>

      {/* ===== Ringkasan Pembelian (Buyer) ===== */}
      {hasBuyer && (
        <>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-bold text-lg text-slate-900 flex items-center gap-2">
              <ShoppingCart className="w-5 h-5 text-rural-600" /> Aktivitas Pembelian
            </h2>
            <Link to="/pesanan" className="text-sm text-rural-600 hover:text-rural-700">
              Semua pesanan saya
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard
              label="Total Pesanan"
              value={buyer.total}
              icon={<User className="w-5 h-5" />}
              tone="blue"
            />
            <StatCard
              label="Menunggu Konfirmasi"
              value={buyer.pending}
              icon={<Clock className="w-5 h-5" />}
              tone="amber"
            />
            <StatCard
              label="Selesai"
              value={buyer.completed}
              icon={<CheckCircle className="w-5 h-5" />}
              tone="rural"
            />
            <StatCard
              label="Pesanan Terbaru"
              value={buyer.recent.length}
              icon={<ShoppingCart className="w-5 h-5" />}
              tone="slate"
            />
          </div>

          <Card className="mb-8">
            <CardHeader>
              <h3 className="font-bold text-slate-900">Pesanan Terbaru (Pembelian)</h3>
            </CardHeader>
            <CardBody className="p-4">
              {buyer.recent.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-6">
                  Belum ada pesanan. Mulai belanja dari katalog produk kami.
                </p>
              ) : (
                <div className="space-y-3">
                  {buyer.recent.map((o) => (
                    <div key={o.id} className="flex justify-between items-center p-3 bg-white border border-slate-100 rounded-xl">
                      <div>
                        <h4 className="font-bold text-slate-900 text-sm">
                          #{o.order_number || o.id}
                        </h4>
                        <p className="text-xs text-slate-500">
                          {formatDate(o.created_at)}
                          {o.seller?.business_name ? ` · ${o.seller.business_name}` : ''}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-slate-900">{formatRupiah(o.total_amount)}</p>
                        <Badge variant={STATUS_BADGE[o.order_status] || 'default'} className="text-xs capitalize">
                          {o.order_status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardBody>
            <CardFooter className="flex gap-2">
              <Button asChild size="sm" variant="outline" className="flex-1">
                <Link to="/pesanan">Pesanan Saya</Link>
              </Button>
              <Button asChild size="sm" variant="outline" className="flex-1">
                <Link to="/pesanan?status=completed">Riwayat Transaksi</Link>
              </Button>
            </CardFooter>
          </Card>
        </>
      )}

      {/* ===== Ringkasan Penjualan (Seller) ===== */}
      {hasSeller && (
        <>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-bold text-lg text-slate-900 flex items-center gap-2">
              <Package className="w-5 h-5 text-rural-600" /> Aktivitas Penjualan
            </h2>
            <Link to="/seller/pesanan" className="text-sm text-rural-600 hover:text-rural-700">
              Semua pesanan masuk
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard
              label="Total Pesanan Masuk"
              value={seller.totalOrders}
              icon={<Truck className="w-5 h-5" />}
              tone="blue"
            />
            <StatCard
              label="Perlu Diproses (Pending)"
              value={seller.pendingOrders}
              icon={<Clock className="w-5 h-5" />}
              tone="amber"
            />
            <StatCard
              label="Jumlah Produk"
              value={seller.totalProducts}
              icon={<Package className="w-5 h-5" />}
              tone="rural"
            />
            <StatCard
              label="Pesanan Terbaru"
              value={seller.recentOrders.length}
              icon={<CheckCircle className="w-5 h-5" />}
              tone="slate"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
            {/* Pesanan masuk terbaru */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <h3 className="font-bold text-slate-900">Pesanan Masuk Terbaru</h3>
              </CardHeader>
              <CardBody className="p-4">
                {seller.recentOrders.length === 0 ? (
                  <p className="text-sm text-slate-500 text-center py-6">
                    Belum ada pesanan masuk.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {seller.recentOrders.map((o) => (
                      <div key={o.id} className="flex justify-between items-center p-3 bg-white border border-slate-100 rounded-xl">
                        <div>
                          <h4 className="font-bold text-slate-900 text-sm">
                            #{o.order_number || o.id}
                          </h4>
                          <p className="text-xs text-slate-500">
                            {formatDate(o.created_at)}
                            {o.buyer?.business_name || o.buyer?.full_name
                              ? ` · ${o.buyer?.business_name || o.buyer?.full_name}`
                              : ''}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="font-medium text-slate-900">{formatRupiah(o.total_amount)}</p>
                          <Badge variant={STATUS_BADGE[o.order_status] || 'default'} className="text-xs capitalize">
                            {o.order_status}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardBody>
              <CardFooter className="flex gap-2">
                <Button asChild size="sm" variant="outline" className="flex-1">
                  <Link to="/seller/pesanan?status=pending">Pesanan Masuk</Link>
                </Button>
                <Button asChild size="sm" variant="outline" className="flex-1">
                  <Link to="/seller/pesanan">Riwayat Penjualan</Link>
                </Button>
              </CardFooter>
            </Card>

            {/* Produk saya */}
            <Card>
              <CardHeader>
                <h3 className="font-bold text-slate-900">Produk Saya</h3>
              </CardHeader>
              <CardBody className="p-4">
                {seller.products.length === 0 ? (
                  <p className="text-sm text-slate-500 text-center py-6">
                    Belum ada produk. Mulai menambahkan produk Anda.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {seller.products.map((p) => (
                      <div key={p.id} className="flex gap-3 items-center p-3 bg-white border border-slate-100 rounded-xl">
                        <div className="w-10 h-10 bg-slate-100 rounded flex items-center justify-center shrink-0">
                          <img
                            src={p.images?.[0]?.url || PRODUCT_IMAGE_PLACEHOLDER}
                            alt={p.product_name}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.target.src = PRODUCT_IMAGE_PLACEHOLDER
                            }}
                          />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-bold text-slate-900 text-sm truncate">{p.product_name}</h4>
                          <p className="text-xs text-slate-500">
                            {formatRupiah(p.price)}/{p.unit || 'kg'}
                          </p>
                        </div>
                        <Badge
                          variant={p.product_status === 'active' ? 'success' : 'default'}
                          className="text-xs"
                        >
                          {p.product_status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardBody>
              <CardFooter>
                <Button asChild size="sm" variant="outline" className="w-full">
                  <Link to="/produk/kelola">Kelola Semua Produk</Link>
                </Button>
              </CardFooter>
            </Card>
          </div>

          {/* Tindakan cepat seller */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Button asChild variant="outline" className="w-full">
              <Link to="/produk/tambah" className="flex items-center gap-2">
                <Plus className="w-4 h-4" /> Tambah Produk
              </Link>
            </Button>
            <Button asChild variant="outline" className="w-full">
              <Link to="/ai/insights" className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4" /> AI Business Insights
              </Link>
            </Button>
            <Button asChild variant="outline" className="w-full">
              <Link to="/profil-bisnis" className="flex items-center gap-2">
                <User className="w-4 h-4" /> Perbarui Profil
              </Link>
            </Button>
          </div>
        </>
      )}

      {/* Pengguna tanpa activity (mis. data error) */}
      {!hasBuyer && !hasSeller && (
        <Card className="p-12 text-center">
          <p className="text-slate-500 mb-4">
            Data dashboard tidak dapat dimuat. Silakan coba lagi.
          </p>
          <Button onClick={loadDashboard}>Muat Ulang</Button>
        </Card>
      )}
    </div>
  )
}
