import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { productService } from '../api/auth'
import { useToast } from '../context/ToastContext'
import { Card } from '../components/ui/Card'
import { CardHeader } from '../components/ui/Card'
import { CardBody } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { ArrowLeft, Plus } from 'lucide-react'
import { ProductForm } from '../components/product/ProductForm'

export default function ProdukEdit() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { success, error } = useToast()
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadProduct()
  }, [id])

  const loadProduct = async () => {
    try {
      const res = await productService.getMyProduct(id)
      setProduct(res.data.data.product || res.data.data || res.data)
    } catch (err) {
      error('Gagal memuat produk: ' + (err.response?.data?.message || err.message))
    } finally {
      setLoading(false)
    }
  }

  const handleSave = (updatedProduct) => {
    success('Produk berhasil diperbarui.')
    setProduct(updatedProduct)
    navigate('/produk/kelola')
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rural-600"></div>
      </div>
    )
  }

  if (!product) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <h2 className="text-slate-900 font-bold mb-2">Produk tidak ditemukan</h2>
          <Button variant="outline" onClick={() => navigate('/produk/kelola')}>
            <ArrowLeft className="w-3 h-3 mr-1" /> Kembali ke Kelola Produk
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="font-display font-bold text-2xl text-slate-900">Edit Produk</h1>
          <p className="text-slate-600">
            Perbarui informasi produk {product.product_name}.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/produk/kelola')}
        >
          <ArrowLeft className="w-3 h-3 mr-1" /> Kembali ke Kelola Produk
        </Button>
      </div>

      <div className="max-w-2xl">
        <Card>
          <CardHeader>
            <h2 className="font-bold text-lg text-slate-900">Informasi Produk</h2>
          </CardHeader>
          <CardBody>
            <ProductForm product={product} onSave={handleSave} />
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
