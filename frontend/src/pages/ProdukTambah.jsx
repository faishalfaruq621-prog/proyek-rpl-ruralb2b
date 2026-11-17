import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { productService } from '../api/auth'
import { useToast } from '../context/ToastContext'
import { Card } from '../components/ui/Card'
import { CardHeader } from '../components/ui/Card'
import { CardBody } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { ArrowLeft, Plus } from 'lucide-react'
import { ProductForm } from '../components/product/ProductForm'

export default function ProdukTambah() {
  const navigate = useNavigate()
  const { success, error } = useToast()
  const [loading, setLoading] = useState(false)

  const handleSave = (product) => {
    success('Produk berhasil ditambahkan.')
    navigate('/produk/kelola')
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    // Form disimpan melalui ProductForm, ini hanya fallback
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="font-display font-bold text-2xl text-slate-900">Tambah Produk</h1>
          <p className="text-slate-600">
            Isi informasi produk yang akan dijual di RuralB2B.
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
            <ProductForm onSave={handleSave} />
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
