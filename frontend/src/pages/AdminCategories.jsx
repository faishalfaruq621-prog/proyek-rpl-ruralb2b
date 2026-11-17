import { useState, useEffect } from 'react'
import { adminService } from '../api/auth'
import { Card, CardBody } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { useToast } from '../context/ToastContext'
import { Tag, Plus, Trash2, Pencil } from 'lucide-react'

const INITIAL_FORM = { name: '', description: '' }

export default function AdminCategories() {
  const { success: toastSuccess, error: toastError } = useToast()
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [form, setForm] = useState(INITIAL_FORM)
  const [editingId, setEditingId] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadCategories()
  }, [])

  const loadCategories = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await adminService.getCategories({ page: 1, per_page: 100 })
      const data = res.data?.data || {}
      setCategories(Array.isArray(data.items) ? data.items : [])
    } catch (err) {
      console.error('Gagal memuat kategori:', err)
      setError(err.response?.data?.message || 'Gagal memuat kategori')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (saving) return
    setSaving(true)
    try {
      if (editingId) {
        await adminService.updateCategory(editingId, form)
        toastSuccess('Kategori berhasil diperbarui.')
      } else {
        await adminService.createCategory(form)
        toastSuccess('Kategori berhasil dibuat.')
      }
      setForm(INITIAL_FORM)
      setEditingId(null)
      await loadCategories()
    } catch (err) {
      const errorDetails = err.response?.data?.errors
      const detail = errorDetails
        ? Object.values(errorDetails).join(' ')
        : err.response?.data?.message
      toastError(detail || 'Gagal menyimpan kategori')
    } finally {
      setSaving(false)
    }
  }

  const startEdit = (cat) => {
    setEditingId(cat.id)
    setForm({ name: cat.name, description: cat.description || '' })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const cancelEdit = () => {
    setEditingId(null)
    setForm(INITIAL_FORM)
  }

  const handleDelete = async (cat) => {
    if (!window.confirm(`Hapus kategori "${cat.name}"?`)) return
    try {
      await adminService.deleteCategory(cat.id)
      toastSuccess('Kategori berhasil dihapus.')
      await loadCategories()
    } catch (err) {
      toastError(
        err.response?.data?.message || 'Kategori masih digunakan sehingga tidak dapat dihapus'
      )
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-rural-600"></div>
          <span className="text-sm text-slate-500">Memuat kategori...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="font-display font-bold text-2xl text-slate-900">Manajemen Kategori</h1>
        <p className="text-slate-600 text-sm">
          Kategori dipakai di katalog dan form produk seller. Hapus hanya bisa untuk kategori tanpa produk.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Form */}
        <Card className="lg:col-span-1 h-fit">
          <CardBody className="p-5">
            <h2 className="font-bold text-lg text-slate-900 mb-4 flex items-center gap-2">
              <Tag className="w-5 h-5 text-rural-600" />
              {editingId ? `Ubah Kategori #${editingId}` : 'Tambah Kategori'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="label">Nama Kategori</label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Pertanian"
                  required
                />
              </div>
              <div>
                <label className="label">Deskripsi (opsional)</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={3}
                  className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-rural-500 outline-none"
                  placeholder="Deskripsi singkat kategori"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  type="submit"
                  disabled={saving}
                  className="flex-1 bg-rural-600 hover:bg-rural-700 text-white"
                >
                  {saving ? 'Menyimpan...' : editingId ? 'Simpan Perubahan' : 'Tambah Kategori'}
                </Button>
                {editingId && (
                  <Button type="button" variant="outline" onClick={cancelEdit}>
                    Batal
                  </Button>
                )}
              </div>
            </form>
          </CardBody>
        </Card>

        {/* Daftar */}
        <div className="lg:col-span-2 space-y-3">
          {error && (
            <Card className="p-6 border-red-100 bg-red-50">
              <p className="text-sm text-red-700">{error}</p>
            </Card>
          )}
          {categories.length === 0 ? (
            <Card className="p-12 text-center">
              <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4 text-slate-400">
                <Plus className="w-8 h-8" />
              </div>
              <h3 className="font-bold text-slate-900 mb-2">Belum ada kategori</h3>
              <p className="text-slate-500">Tambahkan kategori pertama lewat form.</p>
            </Card>
          ) : (
            categories.map((cat) => (
              <Card key={cat.id}>
                <CardBody className="p-4 flex justify-between items-center gap-4">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-bold text-slate-900 text-sm">{cat.name}</p>
                      <Badge variant={cat.parent_id ? 'default' : 'success'} className="text-[10px]">
                        {cat.parent_id ? 'sub-kategori' : 'utama'}
                      </Badge>
                      <span className="text-[11px] text-slate-400">
                        {cat.product_count} produk · {cat.children_count} sub-kategori
                      </span>
                    </div>
                    {cat.description && (
                      <p className="text-xs text-slate-500 truncate">{cat.description}</p>
                    )}
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <Button size="sm" variant="outline" onClick={() => startEdit(cat)}>
                      <Pencil className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={cat.product_count > 0 || cat.children_count > 0}
                      onClick={() => handleDelete(cat)}
                      className="border-red-200 text-red-600 hover:bg-red-50 disabled:opacity-40"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </CardBody>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
