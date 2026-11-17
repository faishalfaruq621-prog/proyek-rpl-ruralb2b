import { useState, useEffect } from 'react'
import { productService } from '../../api/auth'
import { useToast } from '../../context/ToastContext'
import { Card } from '../../components/ui/Card'
import { CardHeader } from '../../components/ui/Card'
import { CardBody } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { Plus, Trash2, Image } from 'lucide-react'

export function ProductForm({ product, onSave, loading = false }) {
  const { success, error } = useToast()
  const [form, setForm] = useState({
    product_name: product?.product_name || '',
    description: product?.description || '',
    category_id: product?.category_id || product?.category?.id || '',
    price: product?.price || '',
    unit: product?.unit || 'kg',
    minimum_order: product?.minimum_order || 1,
    product_status: product?.product_status || 'active',
    stock_quantity: product?.stock_quantity || 0,
  })
  const [images, setImages] = useState(product?.images || [])
  const [newImage, setNewImage] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [categories, setCategories] = useState([])

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const res = await productService.getCategories()
        const data = res.data?.data || {}
        if (mounted) setCategories(Array.isArray(data.items) ? data.items : [])
      } catch (err) {
        // Form tetap bisa disimpan tanpa kategori (opsional).
        console.error('Gagal memuat kategori:', err)
      }
    }
    load()
    return () => {
      mounted = false
    }
  }, [])

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm({ ...form, [name]: value })
  }

  const handleImageChange = (e) => {
    setNewImage(e.target.files?.[0] || null)
  }

  const handleAddImage = async () => {
    if (!newImage) return
    if (!product) {
      error('Simpan produk terlebih dahulu sebelum menambahkan gambar.')
      return
    }
    const formData = new FormData()
    formData.append('file', newImage)
    try {
      const res = await productService.uploadImage(product.id, formData)
      const newImg = res.data.data.image
      setImages([...images, newImg])
      setNewImage(null)
      success('Gambar berhasil diunggah.')
    } catch (err) {
      error(err.response?.data?.message || 'Gagal mengunggah gambar')
    }
  }

  const handleRemoveImage = async (imageId) => {
    if (!product) return
    if (!confirm('Yakin ingin menghapus gambar ini?')) return
    try {
      await productService.deleteImage(product.id, imageId)
      setImages(images.filter((img) => img.id !== imageId))
      success('Gambar berhasil dihapus.')
    } catch (err) {
      error(err.response?.data?.message || 'Gagal menghapus gambar')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const payload = {
        product_name: form.product_name,
        description: form.description || undefined,
        category_id: form.category_id ? parseInt(form.category_id) : undefined,
        price: parseFloat(form.price),
        unit: form.unit,
        minimum_order: parseInt(form.minimum_order) || 1,
        product_status: form.product_status,
      }
      if (product) {
        await productService.updateProduct(product.id, payload)
        if (form.stock_quantity !== undefined) {
          await productService.updateInventory(product.id, {
            stock_quantity: parseInt(form.stock_quantity) || 0,
          })
        }
        success('Produk berhasil diperbarui.')
      } else {
        payload.stock_quantity = parseInt(form.stock_quantity) || 0
        const res = await productService.createProduct(payload)
        onSave(res.data.data.product)
        success('Produk berhasil dibuat. Silakan unggah gambar produk.')
      }
    } catch (err) {
      error(err.response?.data?.message || 'Gagal menyimpan produk')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <h2 className="font-bold text-lg text-slate-900">
          {product ? 'Edit Produk' : 'Tambah Produk Baru'}
        </h2>
      </CardHeader>
      <CardBody>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="label">Nama Produk</label>
              <Input
                name="product_name"
                value={form.product_name}
                onChange={handleChange}
                placeholder="Tomat Merah Organik"
                required
              />
            </div>
            <div>
              <label className="label">Satuan</label>
              <Input
                name="unit"
                value={form.unit}
                onChange={handleChange}
                placeholder="kg"
                required
              />
            </div>
            <div>
              <label className="label">Harga (per satuan)</label>
              <Input
                name="price"
                type="number"
                value={form.price}
                onChange={handleChange}
                placeholder="12000"
                required
              />
            </div>
            <div>
              <label className="label">Minimum Order</label>
              <Input
                name="minimum_order"
                type="number"
                value={form.minimum_order}
                onChange={handleChange}
                placeholder="1"
              />
            </div>
            <div>
              <label className="label">Kategori</label>
              <select
                name="category_id"
                value={form.category_id}
                onChange={handleChange}
                className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-rural-500 outline-none bg-white"
              >
                <option value="">Tidak berkategori (opsional)</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
              <p className="text-xs text-slate-400 mt-1">
                Daftar kategori dikelola administrator RuralB2B
              </p>
            </div>
            <div>
              <label className="label">Stok Awal</label>
              <Input
                name="stock_quantity"
                type="number"
                value={form.stock_quantity}
                onChange={handleChange}
                placeholder="100"
              />
            </div>
            <div className="flex items-end">
              <label className="label mr-2">Status Produk</label>
              <select
                name="product_status"
                value={form.product_status}
                onChange={handleChange}
                className="input w-48"
              >
                <option value="active">Aktif</option>
                <option value="inactive">Nonaktif</option>
                <option value="out_of_stock">Habis Stok</option>
              </select>
            </div>
          </div>

          <div>
            <label className="label">Deskripsi</label>
            <Input
              name="description"
              value={form.description}
              onChange={handleChange}
              placeholder="Deskripsi singkat tentang produk Anda..."
              className="h-32"
            />
          </div>

          <Button
            type="submit"
            disabled={submitting}
            className="w-full bg-rural-600 hover:bg-rural-700 text-white py-3"
          >
            {submitting ? 'Menyimpan...' : product ? 'Perbarui Produk' : 'Simpan Produk'}
          </Button>
        </form>
      </CardBody>

      {product && images.length > 0 && (
        <CardBody className="p-4 border-t border-slate-100">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-900 text-sm uppercase tracking-wider">Gambar Produk</h3>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">{images.length}/5 gambar</span>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {images.map((img) => (
              <div key={img.id} className="relative group">
                <img
                  src={img.url}
                  alt={`Gambar ${img.id}`}
                  className="w-full h-24 object-cover rounded-lg border border-slate-200 opacity-80 group-hover:opacity-100"
                  onError={(e) => {
                    e.target.src = 'https://images.unsplash.com/photo-1592676807127-8464be6c912a?q=80&w=800&auto=format&fit=crop'
                  }}
                />
                <button
                  onClick={() => handleRemoveImage(img.id)}
                  className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-red-500 text-white flex items-center justify-center text-xs hover:bg-red-600 transition-colors"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
                {img.is_primary && (
                  <Badge variant="success" className="absolute bottom-1 left-1 text-[10px]">Primary</Badge>
                )}
              </div>
            ))}
            <div
              onClick={() => document.getElementById('image-upload').click()}
              className="aspect-[4/3] w-24 h-24 border-2 border-dashed border-slate-300 rounded-lg flex flex-col items-center justify-center text-slate-400 hover:border-rural-600 hover:text-rural-600 transition-colors cursor-pointer group"
            >
              <input
                id="image-upload"
                type="file"
                accept="image/*"
                onChange={handleImageChange}
                className="hidden"
              />
              <Plus className="w-5 h-5 mb-1" />
              <span className="text-xs font-medium">Tambah Gambar</span>
            </div>
          </div>
          {newImage && (
            <Button
              onClick={handleAddImage}
              size="sm"
              variant="outline"
              className="w-full"
            >
              <Image className="w-4 h-4 mr-2" /> Unggah Gambar Dipilih
            </Button>
          )}
        </CardBody>
      )}
    </Card>
  )
}
