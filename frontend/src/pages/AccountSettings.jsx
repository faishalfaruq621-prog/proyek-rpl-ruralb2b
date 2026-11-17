import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { authService, businessProfileService } from '../api/auth'
import { Card, CardHeader, CardBody } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { getCapabilities } from '../utils/capabilities'
import TelegramSettings from '../components/admin/TelegramSettings'
import {
  User,
  ShieldCheck,
  KeyRound,
  ToggleLeft,
  ArrowRight,
} from 'lucide-react'

export default function AccountSettings() {
  const { user } = useAuth()
  const caps = getCapabilities(user)
  const { error: toastError, success: toastSuccess } = useToast()

  // ===== Perubahan password =====
  const [pwForm, setPwForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })
  const [changingPw, setChangingPw] = useState(false)

  // ===== Kemampuan akun =====
  const [capsState, setCapsState] = useState({ can_buy: true, can_sell: true })
  const [savingCaps, setSavingCaps] = useState(false)
  const [profileExists, setProfileExists] = useState(false)
  const [profileVerified, setProfileVerified] = useState(null)

  useEffect(() => {
    // Admin tidak punya profil bisnis — hindari panggilan yang pasti 404.
    if (user?.role === 'admin') return
    const loadCapabilities = async () => {
      try {
        const res = await businessProfileService.getProfile()
        const profile = res.data?.data?.profile || null
        if (profile) {
          setProfileExists(true)
          setCapsState({
            can_buy: profile.can_buy !== false,
            can_sell: profile.can_sell !== false,
          })
          setProfileVerified(res.data?.data?.verification || null)
        }
      } catch (err) {
        // Profil bisa belum ada; tombol kemampuan tetap tidak aktif.
        setProfileExists(false)
      }
    }
    loadCapabilities()
  }, [user?.role])

  const handleChangePw = async (e) => {
    e.preventDefault()
    if (changingPw) return
    if (pwForm.new_password !== pwForm.confirm_password) {
      toastError('Konfirmasi password baru tidak sama.')
      return
    }
    setChangingPw(true)
    try {
      await authService.changePassword({
        current_password: pwForm.current_password,
        new_password: pwForm.new_password,
      })
      toastSuccess('Password berhasil diubah.')
      setPwForm({ current_password: '', new_password: '', confirm_password: '' })
    } catch (err) {
      toastError(err.response?.data?.message || 'Gagal mengubah password')
    } finally {
      setChangingPw(false)
    }
  }

  const toggleCapability = async (field) => {
    if (savingCaps || !profileExists) return
    const next = { ...capsState, [field]: !capsState[field] }
    if (!next.can_buy && !next.can_sell) {
      toastError('Salah satu kemampuan (beli atau jual) harus tetap aktif.')
      return
    }
    if (
      !window.confirm(
        field === 'can_sell'
          ? 'Nonaktifkan kemampuan menjual? Menu penjualan akan disembunyikan dan akses halaman penjual ditolak.'
          : 'Nonaktifkan kemampuan membeli? Menu pembelian akan disembunyikan dan akses halaman pembeli ditolak.'
      )
    )
      return

    setSavingCaps(true)
    try {
      await businessProfileService.updateProfile({ [field]: next[field] })
      setCapsState(next)
      toastSuccess(
        field === 'can_sell'
          ? next.can_sell
            ? 'Kemampuan menjual aktif kembali.'
            : 'Kemampuan menjual dinonaktifkan.'
          : next.can_buy
            ? 'Kemampuan membeli aktif kembali.'
            : 'Kemampuan membeli dinonaktifkan.'
      )
      // Segarkan halaman agar Navbar membaca capability terbaru dari profil.
      window.location.reload()
    } catch (err) {
      toastError(
        err.response?.data?.message || 'Gagal mengubah kemampuan akun'
      )
    } finally {
      setSavingCaps(false)
    }
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="font-display font-bold text-2xl text-slate-900">
          Pengaturan Akun
        </h1>
        <p className="text-slate-600">
          Informasi akun, keamanan, dan kemampuan bela/jual Anda.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-5xl">
        {/* ===== Informasi akun ===== */}
        <Card>
          <CardHeader>
            <h2 className="font-bold text-lg text-slate-900 flex items-center gap-2">
              <User className="w-5 h-5 text-rural-600" /> Informasi Akun
            </h2>
          </CardHeader>
          <CardBody className="p-5 space-y-3 text-sm">
            <div className="flex justify-between gap-3">
              <span className="text-slate-600 shrink-0">Nama Lengkap</span>
              <span className="font-medium text-slate-900 text-right">
                {user?.full_name || '-'}
              </span>
            </div>
            <div className="flex justify-between gap-3">
              <span className="text-slate-600 shrink-0">Email</span>
              <span className="font-medium text-slate-900 text-right break-all">
                {user?.email || '-'}
              </span>
            </div>
            <div className="flex justify-between gap-3">
              <span className="text-slate-600 shrink-0">Status Akun</span>
              <Badge
                variant={user?.account_status === 'active' ? 'success' : 'warning'}
                className="capitalize"
              >
                {user?.account_status || '-'}
              </Badge>
            </div>
            <div className="flex justify-between gap-3">
              <span className="text-slate-600 shrink-0">Tipe Akun</span>
              <span className="font-medium text-slate-900">
                {user?.role === 'admin' ? 'Administrator' : 'Akun Bisnis (UMKM)'}
              </span>
            </div>
            <div className="pt-3 border-t border-slate-100">
              <Button asChild variant="outline" size="sm" className="w-full">
                <Link to="/profil-bisnis" className="justify-between w-full">
                  Edit Profil Bisnis <ArrowRight className="w-4 h-4" />
                </Link>
              </Button>
            </div>
          </CardBody>
        </Card>

        {/* ===== Perubahan password ===== */}
        <Card>
          <CardHeader>
            <h2 className="font-bold text-lg text-slate-900 flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-rural-600" /> Ubah Password
            </h2>
          </CardHeader>
          <CardBody className="p-5">
            <form onSubmit={handleChangePw} className="space-y-4">
              <div>
                <label className="label">Password Saat Ini</label>
                <Input
                  type="password"
                  value={pwForm.current_password}
                  onChange={(e) =>
                    setPwForm({ ...pwForm, current_password: e.target.value })
                  }
                  required
                />
              </div>
              <div>
                <label className="label">Password Baru</label>
                <Input
                  type="password"
                  value={pwForm.new_password}
                  onChange={(e) =>
                    setPwForm({ ...pwForm, new_password: e.target.value })
                  }
                  required
                />
              </div>
              <div>
                <label className="label">Konfirmasi Password Baru</label>
                <Input
                  type="password"
                  value={pwForm.confirm_password}
                  onChange={(e) =>
                    setPwForm({ ...pwForm, confirm_password: e.target.value })
                  }
                  required
                />
              </div>
              <Button
                type="submit"
                disabled={changingPw}
                className="w-full bg-rural-600 hover:bg-rural-700 text-white"
              >
                {changingPw ? 'Menyimpan...' : 'Simpan Password Baru'}
              </Button>
            </form>
          </CardBody>
        </Card>

        {/* ===== Kemampuan akun ===== */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <h2 className="font-bold text-lg text-slate-900 flex items-center gap-2">
              <ToggleLeft className="w-5 h-5 text-rural-600" /> Kemampuan Akun
            </h2>
          </CardHeader>
          <CardBody className="p-5">
            {profileExists ? (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between p-4 border border-slate-200 rounded-xl">
                    <div className="pr-3">
                      <p className="font-bold text-slate-900 text-sm">Beli (Buyer)</p>
                      <p className="text-xs text-slate-500">
                        Menu pembelian: katalog, keranjang, checkout, pesanan saya.
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant={capsState.can_buy ? 'primary' : 'outline'}
                      onClick={() => toggleCapability('can_buy')}
                      disabled={savingCaps}
                      className={`${
                        capsState.can_buy
                          ? 'bg-rural-600 hover:bg-rural-700 text-white'
                          : 'border border-slate-300 text-slate-600'
                      }`}
                    >
                      {capsState.can_buy ? 'Aktif' : 'Nonaktif'}
                    </Button>
                  </div>
                  <div className="flex items-center justify-between p-4 border border-slate-200 rounded-xl">
                    <div className="pr-3">
                      <p className="font-bold text-slate-900 text-sm">Jual (Seller)</p>
                      <p className="text-xs text-slate-500">
                        Menu penjualan: dashboard, produk, pesanan masuk, insight.
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant={capsState.can_sell ? 'primary' : 'outline'}
                      onClick={() => toggleCapability('can_sell')}
                      disabled={savingCaps}
                      className={`${
                        capsState.can_sell
                          ? 'bg-rural-600 hover:bg-rural-700 text-white'
                          : 'border border-slate-300 text-slate-600'
                      }`}
                    >
                      {capsState.can_sell ? 'Aktif' : 'Nonaktif'}
                    </Button>
                  </div>
                </div>
                {profileVerified && (
                  <p className="mt-3 text-xs text-slate-500 flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5 text-rural-500" />
                    Status verifikasi bisnis:{' '}
                    <span className="capitalize">{profileVerified.status || 'belum mengajukan'}</span>
                  </p>
                )}
              </>
            ) : (
              <p className="text-sm text-slate-500">
                Profil bisnis belum tersedia, kemampuan akun belum dapat diatur.
              </p>
            )}
          </CardBody>
        </Card>

        {/* ===== Preferensi Notifikasi — Integrasi Telegram (khusus Admin) ===== */}
        {user?.role === 'admin' && (
          <div className="lg:col-span-2">
            <TelegramSettings />
          </div>
        )}
      </div>
    </div>
  )
}
