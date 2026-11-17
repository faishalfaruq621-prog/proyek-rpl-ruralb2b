import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authService } from '../api/auth'
import { RegisterForm } from '../components/auth/LoginRegisterForms'
import { Card } from '../components/ui/Card'
import { CardHeader } from '../components/ui/Card'
import { CardBody } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { useToast } from '../context/ToastContext'
import { ArrowRight, UserPlus } from 'lucide-react'

export default function Register() {
  const { register } = useAuth()
  const { error: toastError, success: toastSuccess } = useToast()
  const navigate = useNavigate()

  const handleRegister = async (form) => {
    try {
      await register(form)
      toastSuccess('Registrasi berhasil. Silakan masuk.')
      navigate('/login', { replace: true })
    } catch (err) {
      const data = err.response?.data
      if (data?.errors) {
        const firstError = Object.values(data.errors)[0]
        toastError(typeof firstError === 'string' ? firstError : data.message || 'Validasi gagal.')
      } else {
        toastError(data?.message || 'Registrasi gagal. Silakan coba lagi.')
      }
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-earth-50 px-4">
      <Card className="w-full max-w-md shadow-rural-lg">
        <CardHeader className="text-center">
          <div className="w-10 h-10 rounded-xl bg-rural-600 flex items-center justify-center text-white font-bold mx-auto mb-3">
            <UserPlus className="w-5 h-5" />
          </div>
          <h1 className="font-display font-bold text-2xl text-slate-900">Daftar Akun</h1>
          <p className="text-sm text-slate-500 mt-2">
            Bergabunglah sebagai pembeli atau penjual UMKM
          </p>
        </CardHeader>
        <CardBody>
          <RegisterForm onRegister={handleRegister} />
        </CardBody>
        <CardBody className="pt-0 border-t border-slate-100 text-center">
          <p className="text-sm text-slate-600">
            Sudah punya akun?{' '}
            <button onClick={() => navigate('/login')} className="font-medium text-rural-600 hover:text-rural-700">
              Masuk di sini
            </button>
          </p>
        </CardBody>
      </Card>
    </div>
  )
}
