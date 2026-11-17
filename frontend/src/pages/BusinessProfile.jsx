import { useState } from 'react'
import { Link } from 'react-router-dom'
import { businessProfileService } from '../api/auth'
import { Card } from '../components/ui/Card'
import { CardHeader } from '../components/ui/Card'
import { CardBody } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { User, Building2, Phone, MapPin, FileText, Clock } from 'lucide-react'

export default function BusinessProfile() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({
    business_name: '',
    business_type: 'farmer',
    phone: '',
    address: '',
    village: '',
    district: '',
    city: '',
    province: '',
    postal_code: '',
    description: '',
  })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadProfile = async () => {
    try {
      const res = await businessProfileService.getProfile()
      const data = res.data.data.profile || res.data.data || res.data
      setProfile(data)
      setForm({
        business_name: data.business_name || '',
        business_type: data.business_type || 'farmer',
        phone: data.phone || '',
        address: data.address || '',
        village: data.village || '',
        district: data.district || '',
        city: data.city || '',
        province: data.province || '',
        postal_code: data.postal_code || '',
        description: data.description || '',
      })
    } catch (err) {
      console.error('Gagal memuat profil:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleUpdate = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    try {
      await businessProfileService.updateProfile(form)
      setSuccess('Profil bisnis berhasil diperbarui.')
      loadProfile()
    } catch (err) {
      setError(err.response?.data?.message || 'Gagal memperbarui profil.')
    }
  }

  const businessTypes = [
    { value: 'farmer', label: 'Petani' },
    { value: 'supplier', label: 'Supplier' },
    { value: 'collector', label: 'Pengumpul' },
    { value: 'producer', label: 'Produsen' },
    { value: 'shop', label: 'Toko' },
    { value: 'warung', label: 'Warung' },
    { value: 'other', label: 'Lainnya' },
  ]

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rural-600"></div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="font-display font-bold text-2xl text-slate-900">Profil Bisnis</h1>
        <Link to="/dashboard" className="text-sm text-rural-600 hover:text-rural-700">
          Kembali ke Dashboard
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <h2 className="font-bold text-lg text-slate-900">Informasi Bisnis</h2>
            </CardHeader>
            <CardBody>
              {error && (
                <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700 border border-red-100 mb-4">{error}</div>
              )}
              {success && (
                <div className="rounded-lg bg-rural-50 p-4 text-sm text-rural-700 border border-rural-100 mb-4">{success}</div>
              )}
              <form onSubmit={handleUpdate} className="space-y-6">
                <div>
                  <label className="label">Nama Bisnis</label>
                  <Input
                    type="text"
                    placeholder="Tani Makmur"
                    value={form.business_name}
                    onChange={(e) => setForm({ ...form, business_name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="label">Jenis Bisnis</label>
                  <select
                    className="input"
                    value={form.business_type}
                    onChange={(e) => setForm({ ...form, business_type: e.target.value })}
                  >
                    {businessTypes.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">Nomor Telepon</label>
                  <Input
                    type="tel"
                    placeholder="+62 812-3456-7890"
                    value={form.phone}
                    onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  />
                </div>
                <div>
                  <label className="label">Deskripsi Bisnis</label>
                  <Input
                    type="text"
                    placeholder="Produsen sayuran organik"
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                  />
                </div>
                <Button type="submit" className="w-full bg-rural-600 hover:bg-rural-700 text-white py-3">
                  Simpan Perubahan
                </Button>
              </form>
            </CardBody>
          </Card>
        </div>

        <div className="lg:col-span-1">
          <Card className="bg-rural-50 border border-rural-100">
            <CardHeader>
              <h2 className="font-bold text-lg text-rural-900">Status Verifikasi</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-rural-100 flex items-center justify-center text-rural-600">
                  <User className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-bold text-sm text-slate-900">{profile?.business_name || '-'}</p>
                  <p className="text-xs text-slate-500 capitalize">{profile?.business_type || '-'}</p>
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600">Nomor Telepon</span>
                  <span className="text-slate-900 font-medium">{profile?.phone || '-'}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600">Alamat</span>
                  <span className="text-slate-900 font-medium truncate max-w-[200px]">{profile?.address || '-'}</span>
                </div>
              </div>
              <div className="pt-4 border-t border-slate-100">
                <p className="text-xs text-slate-500 uppercase mb-2">Ajukan Verifikasi</p>
                <p className="text-xs text-slate-600 mb-3">
                  Ajukan verifikasi bisnis untuk mendapatkan badge terverifikasi dan
                  meningkatkan kepercayaan pembeli.
                </p>
                <Button size="sm" variant="outline" asChild>
                  <Link to="/verifikasi">Ajukan Sekarang</Link>
                </Button>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  )
}
