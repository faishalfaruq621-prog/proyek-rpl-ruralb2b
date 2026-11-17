import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { adminService } from '../api/auth'
import { useToast } from '../context/ToastContext'
import { Card } from '../components/ui/Card'
import { CardHeader } from '../components/ui/Card'
import { CardBody } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { formatDate } from '../utils/format'
import { Search, User, Clock, ShieldCheck, AlertTriangle, List } from 'lucide-react'

export default function VerifikasiAdmin() {
  const { success, error } = useToast()

  const [verifications, setVerifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('pending')
  const [search, setSearch] = useState('')

  const loadVerifications = async () => {
    try {
      setLoading(true)
      const params = {}
      if (statusFilter) params.status = statusFilter
      if (search) params.q = search
      const res = await adminService.getVerifications(params)
      setVerifications(res.data.data.items || res.data.data || [])
    } catch (err) {
      error('Gagal memuat verifikasi: ' + (err.response?.data?.message || err.message))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadVerifications()
  }, [statusFilter, search])

  const handleApprove = async (id, notes = '') => {
    if (!notes) {
      error('Catatan verifikasi wajib diisi saat menyetujui.')
      return
    }
    try {
      await adminService.approveVerification(id, { notes })
      success('Pengajuan verifikasi disetujui.')
      loadVerifications()
    } catch (err) {
      error(err.response?.data?.message || 'Gagal menyetujui verifikasi')
    }
  }

  const handleReject = async (id, reason) => {
    if (!reason) {
      error('Alasan penolakan wajib diisi.')
      return
    }
    try {
      await adminService.rejectVerification(id, { rejection_reason: reason })
      success('Pengajuan verifikasi ditolak.')
      loadVerifications()
    } catch (err) {
      error(err.response?.data?.message || 'Gagal menolak verifikasi')
    }
  }

  const statusBadge = (status) => {
    const variants = {
      pending: 'warning',
      approved: 'success',
      rejected: 'danger',
    }
    const labels = {
      pending: 'Menunggu',
      approved: 'Disetujui',
      rejected: 'Ditolak',
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
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="font-display font-bold text-2xl text-slate-900">Pengelolaan Verifikasi</h1>
          <p className="text-slate-600">
            Tinjau dan kelola pengajuan verifikasi UMKM dari seluruh platform.
          </p>
        </div>
        <Link to="/dashboard" className="text-sm text-rural-600 hover:text-rural-700">
          Kembali ke Dashboard Admin
        </Link>
      </div>

      {/* Filter */}
      <div className="flex flex-col lg:flex-row gap-4 mb-6 items-end">
        <div className="relative flex-1 lg:w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Cari nama bisnis atau pemilik..."
            className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-rural-500 focus:border-rural-500 outline-none text-sm"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          {['pending', 'approved', 'rejected', ''].map((status) => (
            <Button
              key={status}
              size="sm"
              variant={statusFilter === status ? 'primary' : 'outline'}
              className={`${statusFilter === status ? 'text-white' : 'text-slate-600'} ${
                status === '' ? 'px-4' : 'px-3'
              }`}
              onClick={() => setStatusFilter(status)}
            >
              {status === '' ? 'Semua' : status.charAt(0).toUpperCase() + status.slice(1)}
            </Button>
          ))}
        </div>
      </div>

      {verifications.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4 text-slate-400">
            <List className="w-8 h-8" />
          </div>
          <h3 className="font-bold text-slate-900 mb-2">Tidak ada pengajuan</h3>
          <p className="text-slate-500 mb-6">
            Belum ada pengajuan verifikasi dengan filter yang dipilih.
          </p>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">ID</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Bisnis</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Pemilik</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Diajukan</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {verifications.map((v) => (
                <tr key={v.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 text-sm text-slate-900">#{v.id}</td>
                  <td className="px-4 py-3">
                    <div className="text-sm font-medium text-slate-900">{v.business_profile?.business_name || '-'}</div>
                    <div className="text-xs text-slate-500 capitalize">{v.business_profile?.business_type || '-'}</div>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600">{v.user?.full_name || v.user?.email || '-'}</td>
                  <td className="px-4 py-3">{statusBadge(v.status)}</td>
                  <td className="px-4 py-3 text-sm text-slate-500">{formatDate(v.submitted_at || v.created_at)}</td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      size="sm"
                      variant="outline"
                      asChild
                      className="text-rural-600 hover:text-rural-700"
                    >
                      <Link to={`/verifikasi/admin/${v.id}`}>Detail</Link>
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
