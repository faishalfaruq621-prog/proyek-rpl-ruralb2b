import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authService } from '../api/auth'
import { LoginForm, RegisterForm } from '../components/auth/LoginRegisterForms'
import { Card } from '../components/ui/Card'
import { CardHeader } from '../components/ui/Card'
import { CardBody } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { useToast } from '../context/ToastContext'
import { ArrowRight, Mail, Phone, MapPin } from 'lucide-react'

export default function Login() {
  const { login } = useAuth()
  const { error: toastError, success: toastSuccess } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [view, setView] = useState('login')

  const from = location.state?.from?.pathname || '/'

  const handleLogin = async (form) => {
    try {
      await login(form)
      toastSuccess('Login berhasil. Selamat datang kembali!')
      navigate(from, { replace: true })
    } catch (err) {
      if (!err.response) {
        // Koneksi gagal sebelum server menjawab (backend mati, CORS
        // diblokir, jaringan terputus) — tampilkan penyebab sebenarnya.
        toastError(
          'Tidak dapat terhubung ke server. Pastikan backend berjalan dan halaman dibuka dari alamat yang diizinkan.'
        )
      } else {
        // Server menjawab: tampilkan pesan error asli dari backend.
        toastError(err.response?.data?.message || `Login gagal (HTTP ${err.response.status}).`)
      }
    }
  }

  const handleRegister = async (form) => {
    try {
      await authService.register(form)
      toastSuccess('Registrasi berhasil. Silakan masuk.')
      setView('login')
    } catch (err) {
      toastError(err.response?.data?.message || 'Registrasi gagal. Silakan coba lagi.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-earth-50 px-4">
      <Card className="w-full max-w-md shadow-rural-lg">
        <CardHeader className="text-center">
          <h1 className="font-display font-bold text-2xl text-slate-900">
            {view === 'login' ? 'Selamat Datang Kembali' : 'Buat Akun Baru'}
          </h1>
          <p className="text-sm text-slate-500 mt-2">
            {view === 'login'
              ? 'Masuk ke akun RuralB2B Anda'
              : 'Bergabunglah sebagai pembeli atau penjual'}
          </p>
        </CardHeader>
        <CardBody className="space-y-6">
          {view === 'login' ? (
            <LoginForm onLogin={handleLogin} />
          ) : (
            <RegisterForm onRegister={handleRegister} />
          )}
          <div className="text-center pt-4 border-t border-slate-100">
            <p className="text-sm text-slate-600">
              {view === 'login'
                ? 'Belum punya akun? '
                : 'Sudah punya akun? '}
              <button
                onClick={() => setView(view === 'login' ? 'register' : 'login')}
                className="font-medium text-rural-600 hover:text-rural-700"
              >
                {view === 'login' ? 'Daftar di sini' : 'Masuk di sini'}
              </button>
            </p>
          </div>
        </CardBody>
      </Card>

      <div className="max-w-md mt-8">
        <Card className="!bg-rural-900 !border-rural-800 text-white">
          <div className="flex gap-4 mb-4">
            <div className="w-10 h-10 rounded-xl bg-rural-600 flex items-center justify-center">
              <HandshakeIcon />
            </div>
            <div>
              <h3 className="font-bold text-lg">Beli Langsung dari Sumber</h3>
              <p className="text-sm text-rural-200">Tanpa perantara berlebihan</p>
            </div>
          </div>
          <div className="flex gap-4 mb-4">
            <div className="w-10 h-10 rounded-xl bg-rural-600 flex items-center justify-center">
              <ShieldCheckIcon />
            </div>
            <div>
              <h3 className="font-bold text-lg">Transaksi Terpercaya</h3>
              <p className="text-sm text-rural-200">Bukti pembayaran divalidasi penjual</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}

function HandshakeIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}
function ShieldCheckIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}
