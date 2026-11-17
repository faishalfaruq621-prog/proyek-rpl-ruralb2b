import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { productService } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { Card } from '../components/ui/Card'
import { CardHeader } from '../components/ui/Card'
import { CardBody } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { formatRupiah, PRODUCT_IMAGE_PLACEHOLDER } from '../utils/format'
import { Edit, Trash2, Plus, Package, Search, RefreshCw } from 'lucide-react'

export default function ProdukKelola() {
  const { user } = useAuth()
  const { success, error } = useToast()
  const navigate = useNavigate()

  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const loadProducts = async () => {
    try {
      setLoading(true)
      const params = {}
      if (search) params.q = search
      if (statusFilter) params.status = statusFilter
      const res = await productService.getMyProducts(params)
      setProducts(res.data.data.items || res.data.data || [])
    } catch (err) {
      error('Gagal memuat produk: ' + (err.response?.data?.message || err.message))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProducts()
  }, [search, statusFilter])

  const handleDelete = async (id) => {
    if (!confirm('Yakin ingin menghapus produk ini?')) return
    try {
      await productService.deleteProduct(id)
      success('Produk berhasil dihapus.')
      setProducts(products.filter((p) => p.id !== id))
    } catch (err) {
      error(err.response?.data?.message || 'Gagal menghapus produk')
    }
  }

  const handleToggleStatus = async (product) => {
    const newStatus = product.product_status === 'active' ? 'inactive' : 'active'
    try {
      await productService.updateProduct(product.id, { product_status: newStatus })
      success(`Produk berhasil di${newStatus === 'active' ? 'aktifkan' : 'nonaktifkan'}.`)
      setProducts(products.map((p) => (p.id === product.id ? { ...p, product_status: newStatus } : p)))
    } catch (err) {
      error(err.response?.data?.message || 'Gagal mengubah status produk')
    }
  }

  const statusBadge = (status) => {
    const variants = {
      active: 'success',
      inactive: 'default',
      out_of_stock: 'warning',
    }
    const labels = {
      active: 'Aktif',
      inactive: 'Nonaktif',
      out_of_stock: 'Habis Stok',
    }
    return <Badge variant={variants[status] || 'default'}>{labels[status] || status}</Badge>
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
      <div className="flex flex-col lg:flex-row gap-6 justify-between items-end mb-8">
        <div>
          <h1 className="font-display font-bold text-2xl text-slate-900">Kelola Produk</h1>
          <p className="text-slate-600">
            Kelola produk yang Anda jual di RuralB2B.
          </p>
        </div>
        <div className="flex gap-3">
          <Button size="sm" asChild>
            <Link to="/produk/tambah">
              <Plus className="w-3 h-3 mr-1" /> Tambah Produk
            </Link>
          </Button>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Cari produk..."
              className="w-64 pl-10 pr-4 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-rural-500 focus:border-rural-500 outline-none text-sm"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-white border border-slate-200 text-slate-700 text-sm rounded-xl px-3 py-2 focus:ring-2 focus:ring-rural-500 outline-none cursor-pointer"
          >
            <option value="">Semua Status</option>
            <option value="active">Aktif</option>
            <option value="inactive">Nonaktif</option>
            <option value="out_of_stock">Habis Stok</option>
          </select>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setSearch('')
              setStatusFilter('')
              loadProducts()
            }}
          >
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {products.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4 text-slate-400">
            <Package className="w-8 h-8" />
          </div>
          <h3 className="font-bold text-slate-900 mb-2">Belum ada produk</h3>
          <p className="text-slate-500 mb-6">
            Mulai menambahkan produk Anda ke marketplace RuralB2B.
          </p>
          <Button className="bg-rural-600 hover:bg-rural-700 text-white" asChild>
            <Link to="/produk/tambah">Tambah Produk Pertama</Link>
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {products.map((product) => (
            <Card key={product.id} className="hover:border-rural-200 transition-border">
              <div className="h-40 bg-slate-100 flex items-center justify-center overflow-hidden mb-4 relative">
                <img
                  src={product.images?.[0]?.url || PRODUCT_IMAGE_PLACEHOLDER}
                  alt={product.product_name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.target.src = PRODUCT_IMAGE_PLACEHOLDER
                  }}
                />
                <div className="absolute top-2 right-2">
                  {statusBadge(product.product_status)}
                </div>
              </div>
              <div className="p-4">
                <h3 className="font-bold text-slate-900 text-base line-clamp-1 mb-1">
                  {product.product_name}
                </h3>
                <p className="text-xs text-slate-500 truncate mb-3">
                  {product.description || '-'}
                </p>
                <div className="flex justify-between items-baseline mb-4">
                  <span className="font-bold text-rural-600 text-lg">
                    {formatRupiah(product.price)}
                  </span>
                  <span className="text-xs text-slate-500">/{product.unit || 'kg'}</span>
                </div>
                <div className="space-y-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full"
                    onClick={() => navigate(`/produk/edit/${product.id}`)}
                  >
                    <Edit className="w-3 h-3 mr-1" /> Edit
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full text-red-500 hover:bg-red-50"
                    onClick={() => handleDelete(product.id)}
                  >
                    <Trash2 className="w-3 h-3 mr-1" /> Hapus
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full"
                    onClick={() => handleToggleStatus(product)}
                  >
                    {product.product_status === 'active' ? 'Nonaktifkan' : 'Aktifkan'}
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
