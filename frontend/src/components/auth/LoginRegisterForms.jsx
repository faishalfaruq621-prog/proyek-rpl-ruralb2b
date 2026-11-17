import { useState } from 'react'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'

export function LoginForm({ onLogin }) {
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await onLogin(form)
    } catch (err) {
      setError(err.response?.data?.message || 'Login gagal. Silakan coba lagi.')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700 border border-red-100">
          {error}
        </div>
      )}
      <div>
        <label className="label">Email</label>
        <Input
          type="email"
          placeholder="email@example.com"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
      </div>
      <div>
        <label className="label">Password</label>
        <Input
          type="password"
          placeholder="••••••••"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />
      </div>
      <Button type="submit" className="w-full" disabled={!form.email || !form.password}>
        Masuk
      </Button>
    </form>
  )
}

export function RegisterForm({ onRegister }) {
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    business_type: 'farmer',
    business_name: '',
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
  const [fieldErrors, setFieldErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)

  const businessTypes = [
    { value: 'farmer', label: 'Petani' },
    { value: 'supplier', label: 'Supplier' },
    { value: 'collector', label: 'Pengumpul' },
    { value: 'producer', label: 'Produsen' },
    { value: 'shop', label: 'Toko' },
    { value: 'warung', label: 'Warung' },
    { value: 'other', label: 'Lainnya' },
  ]

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setFieldErrors({})
    setSubmitting(true)
    try {
      await onRegister(form)
    } catch (err) {
      const data = err.response?.data
      if (data?.errors) {
        setFieldErrors(data.errors)
        const firstError = Object.values(data.errors)[0]
        setError(typeof firstError === 'string' ? firstError : 'Validasi gagal.')
      } else {
        setError(data?.message || 'Registrasi gagal. Silakan coba lagi.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700 border border-red-100">
          {error}
        </div>
      )}
      <div>
        <label className="label">Nama Lengkap</label>
        <Input
          type="text"
          placeholder="Budi Santoso"
          value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          required
          className={fieldErrors.full_name ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}
        />
        {fieldErrors.full_name && (
          <p className="text-xs text-red-600 mt-1">{fieldErrors.full_name}</p>
        )}
      </div>
      <div>
        <label className="label">Email</label>
        <Input
          type="email"
          placeholder="email@example.com"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
          className={fieldErrors.email ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}
        />
        {fieldErrors.email && (
          <p className="text-xs text-red-600 mt-1">{fieldErrors.email}</p>
        )}
      </div>
      <div>
        <label className="label">Password</label>
        <Input
          type="password"
          placeholder="Minimal 8 karakter"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
          className={fieldErrors.password ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}
        />
        {fieldErrors.password && (
          <p className="text-xs text-red-600 mt-1">{fieldErrors.password}</p>
        )}
        <p className="text-xs text-slate-500 mt-1">
          Syarat: minimal 8 karakter, huruf kecil, huruf besar, angka, dan karakter khusus.
        </p>
      </div>
      <div>
        <label className="label">Nama Bisnis</label>
        <Input
          type="text"
          placeholder="Tani Makmur"
          value={form.business_name}
          onChange={(e) => setForm({ ...form, business_name: e.target.value })}
        />
      </div>
      <div>
        <label className="label">Jenis Bisnis</label>
        <select
          className={`input ${fieldErrors.business_type ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
          value={form.business_type}
          onChange={(e) => setForm({ ...form, business_type: e.target.value })}
        >
          {businessTypes.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
        {fieldErrors.business_type && (
          <p className="text-xs text-red-600 mt-1">{fieldErrors.business_type}</p>
        )}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Provinsi</label>
          <Input
            type="text"
            placeholder="Jawa Barat"
            value={form.province}
            onChange={(e) => setForm({ ...form, province: e.target.value })}
          />
          {fieldErrors.province && (
            <p className="text-xs text-red-600 mt-1">{fieldErrors.province}</p>
          )}
        </div>
        <div>
          <label className="label">Kota/Kabupaten</label>
          <Input
            type="text"
            placeholder="Bandung"
            value={form.city}
            onChange={(e) => setForm({ ...form, city: e.target.value })}
          />
          {fieldErrors.city && (
            <p className="text-xs text-red-600 mt-1">{fieldErrors.city}</p>
          )}
        </div>
      </div>
      <div>
        <label className="label">Alamat Lengkap</label>
        <Input
          type="text"
          placeholder="Jl. Raya Desa No. 1, Sukamaju, Cibiru"
          value={form.address}
          onChange={(e) => setForm({ ...form, address: e.target.value })}
        />
        {fieldErrors.address && (
          <p className="text-xs text-red-600 mt-1">{fieldErrors.address}</p>
        )}
      </div>
      <div>
        <label className="label">Deskripsi Bisnis</label>
        <Input
          type="text"
          placeholder="Produsen sayuran organik dari pedesaan"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
        />
        {fieldErrors.description && (
          <p className="text-xs text-red-600 mt-1">{fieldErrors.description}</p>
        )}
      </div>
      <Button type="submit" className="w-full" disabled={submitting || (!form.email || !form.password || !form.full_name)}>
        {submitting ? 'Mendaftar...' : 'Daftar'}
      </Button>
    </form>
  )
}
