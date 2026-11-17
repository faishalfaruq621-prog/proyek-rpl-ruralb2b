import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { adminService } from '../api/auth'
import { Card, CardHeader, CardBody } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { formatRupiah } from '../utils/format'
import { Users, Package, Tag, ShieldCheck, LayoutDashboard } from 'lucide-react'

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await adminService.getStats()
      setStats(res.data?.data || null)
    } catch (err) {
      console.error('Gagal memuat statistik admin:', err)
      setError(err.response?.data?.message || 'Gagal memuat statistik')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-rural-600"></div>
          <span className="text-sm text-slate-500">Memuat statistik...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="p-6 border-red-100 bg-red-50 mb-6">
          <p className="text-sm text-red-700">{error}</p>
        </Card>
        <Button onClick={loadStats}>Muat Ulang</Button>
      </div>
    )
  }

  const statCards = [
    { label: 'Total Pengguna', value: stats?.users?.total ?? 0, link: '/admin/pengguna', icon: <Users className="w-5 h-5" />, tone: 'blue' },
    { label: 'Profil Bisnis', value: stats?.business_profiles?.total ?? 0, link: '/admin/pengguna', icon: <ShieldCheck className="w-5 h-5" />, tone: 'rural' },
    { label: 'Produk', value: stats?.products?.total ?? 0, link: '/admin/kategori', icon: <Package className="w-5 h-5" />, tone: 'amber' },
    { label: 'Kategori', value: stats?.categories?.total ?? 0, link: '/admin/kategori', icon: <Tag className="w-5 h-5" />, tone: 'slate' },
  ]

  const orderSteps = [
    { label: 'Pending', count: stats?.orders?.by_status?.pending ?? 0, tone: 'warning' },
    { label: 'Confirmed', count: stats?.orders?.by_status?.confirmed ?? 0, tone: 'default' },
    { label: 'Processing', count: stats?.orders?.by_status?.processing ?? 0, tone: 'default' },
    { label: 'Shipped', count: stats?.orders?.by_status?.shipped ?? 0, tone: 'default' },
    { label: 'Completed', count: stats?.orders?.by_status?.completed ?? 0, tone: 'success' },
    { label: 'Cancelled', count: stats?.orders?.by_status?.cancelled ?? 0, tone: 'danger' },
  ]

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="font-display font-bold text-2xl text-slate-900">Dashboard Admin</h1>
          <p className="text-slate-600">Statistik platform dihitung langsung dari database.</p>
        </div>
        <LayoutDashboard className="w-10 h-10 text-rural-600 hidden sm:block" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((stat) => (
          <Card key={stat.label} className="p-5">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-xs text-slate-500 uppercase">{stat.label}</p>
                <p className="font-bold text-2xl text-slate-900">{stat.value}</p>
                <Link to={stat.link} className="text-xs text-rural-600 hover:text-rural-700 mt-1 inline-block">
                  Kelola
                </Link>
              </div>
              <div className="w-10 h-10 rounded-lg bg-rural-100 text-rural-600 flex items-center justify-center">
                {stat.icon}
              </div>
            </div>
          </Card>
        ))}
      </div>

      <Card className="mb-8">
        <CardHeader>
          <h2 className="font-bold text-lg text-slate-900">Monitoring Transaksi</h2>
        </CardHeader>
        <CardBody className="p-5">
          <div className="flex flex-wrap items-center gap-3 mb-4">
            {orderSteps.map((step) => (
              <Badge key={step.label} variant={step.tone} className="text-xs capitalize">
                {step.label}: {step.count}
              </Badge>
            ))}
            <span className="text-sm font-bold text-slate-900 ml-2">
              Total: {stats?.orders?.total ?? 0}
            </span>
          </div>
          <Button asChild size="sm" variant="outline">
            <Link to="/admin/transaksi">Lihat Semua Transaksi</Link>
          </Button>
        </CardBody>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Button asChild variant="outline" className="h-20">
          <Link to="/admin/pengguna" className="flex flex-col items-center gap-1">
            <Users className="w-5 h-5" /> Manajemen Pengguna
          </Link>
        </Button>
        <Button asChild variant="outline" className="h-20">
          <Link to="/admin/kategori" className="flex flex-col items-center gap-1">
            <Tag className="w-5 h-5" /> Manajemen Kategori
          </Link>
        </Button>
        <Button asChild variant="outline" className="h-20">
          <Link to="/verifikasi/admin" className="flex flex-col items-center gap-1">
            <ShieldCheck className="w-5 h-5" /> Verifikasi Bisnis
          </Link>
        </Button>
      </div>
    </div>
  )
}
