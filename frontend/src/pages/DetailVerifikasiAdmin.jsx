import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { adminService } from '../api/auth'
import { useToast } from '../context/ToastContext'
import { Card } from '../components/ui/Card'
import { CardHeader } from '../components/ui/Card'
import { CardBody } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { formatDate } from '../utils/format'
import { User, ShieldCheck, Clock, AlertTriangle, FileText, List, Download } from 'lucide-react'

export default function DetailVerifikasiAdmin() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { success, error } = useToast()

  const [verification, setVerification] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDetail()
  }, [id])

  const loadDetail = async () => {
    try {
      setLoading(true)
      const res = await adminService.getVerificationDetail(id)
      setVerification(res.data.data.verification || res.data.data || res.data)
    } catch (err) {
      error('Gagal memuat detail verifikasi: ' + (err.response?.data?.message || err.message))
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async () => {
    const notes = prompt('Masukkan catatan verifikasi (wajib diisi):')
    if (!notes) return
    try {
      await adminService.approveVerification(id, { notes })
      success('Pengajuan verifikasi disetujui.')
      navigate('/verifikasi/admin')
    } catch (err) {
      error(err.response?.data?.message || 'Gagal menyetujui verifikasi')
    }
  }

  const handleReject = async () => {
    const reason = prompt('Masukkan alasan penolakan (wajib diisi):')
    if (!reason) return
    try {
      await adminService.rejectVerification(id, { rejection_reason: reason })
      success('Pengajuan verifikasi ditolak.')
      navigate('/verifikasi/admin')
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

  const downloadDocument = (docId) => {
    window.location.href = `/api/admin/verifications/${id}/documents/${docId}/download`
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rural-600"></div>
      </div>
    )
  }

  if (!verification) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <h2 className="text-slate-900 font-bold mb-2">Verifikasi tidak ditemukan</h2>
          <Button variant="outline" onClick={() => navigate('/verifikasi/admin')}>
            <List className="w-3 h-3 mr-1" /> Kembali ke Daftar
          </Button>
        </div>
      </div>
    )
  }

  const bp = verification.business_profile || {}
  const user = verification.user || {}

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col sm:flex-row sm:justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h1 className="font-display font-bold text-2xl text-slate-900">Detail Verifikasi</h1>
          <p className="text-slate-600">
            Tinjau detail pengajuan verifikasi dan dokumen pendukung.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onClick={() => navigate('/verifikasi/admin')}>
            <List className="w-3 h-3 mr-1" /> Kembali
          </Button>
          {verification.status === 'pending' && (
            <>
              <Button size="sm" variant="outline" onClick={handleReject} className="text-red-500 hover:bg-red-50">
                <AlertTriangle className="w-3 h-3 mr-1" /> Tolak
              </Button>
              <Button size="sm" onClick={handleApprove} className="bg-rural-600 hover:bg-rural-700 text-white">
                <ShieldCheck className="w-3 h-3 mr-1" /> Setujui
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          {/* Info Verifikasi */}
          <Card>
            <CardHeader>
              <h2 className="font-bold text-lg text-slate-900">Informasi Verifikasi</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-3 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-500 uppercase">ID Pengajuan</p>
                  <p className="font-medium text-slate-900">#{verification.id}</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-500 uppercase">Status</p>
                  {statusBadge(verification.status)}
                </div>
                <div className="p-3 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-500 uppercase">Diajukan</p>
                  <p className="font-medium text-slate-900">{formatDate(verification.submitted_at || verification.created_at)}</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-500 uppercase">Reviewed By</p>
                  <p className="font-medium text-slate-900">{verification.reviewed_by ? 'Admin' : '-'}</p>
                </div>
                {verification.reviewed_at && (
                  <div className="p-3 bg-slate-50 rounded-xl">
                    <p className="text-xs text-slate-500 uppercase">Waktu Review</p>
                    <p className="font-medium text-slate-900">{formatDate(verification.reviewed_at)}</p>
                  </div>
                )}
                {verification.rejection_reason && (
                  <div className="p-3 bg-red-50 rounded-xl border border-red-100">
                    <p className="text-xs text-red-500 uppercase">Alasan Penolakan</p>
                    <p className="font-medium text-red-700">{verification.rejection_reason}</p>
                  </div>
                )}
              </div>
            </CardBody>
          </Card>

          {/* Riwayat */}
          {verification.history && verification.history.length > 0 && (
            <Card className="mt-6">
              <CardHeader className="flex justify-between items-center">
                <h2 className="font-bold text-lg text-slate-900">Riwayat Status</h2>
              </CardHeader>
              <CardBody className="p-4">
                <div className="space-y-4">
                  {verification.history.map((h) => (
                    <div key={h.id} className="flex items-start gap-3 p-3 bg-slate-50 rounded-xl">
                      <div className="w-6 h-6 rounded-full bg-slate-200 flex items-center justify-center text-xs font-medium text-slate-600 shrink-0">
                        {h.new_status?.charAt(0).toUpperCase() || '-'}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-slate-900">{h.notes || 'Perubahan status'}</p>
                        <p className="text-xs text-slate-500 mt-1">
                          {h.admin_id ? 'Admin' : 'Sistem'} • {formatDate(h.created_at)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>
          )}
        </div>

        <div className="lg:col-span-1">
          {/* Profil Bisnis */}
          <Card className="bg-rural-50 border border-rural-100">
            <CardHeader>
              <h2 className="font-bold text-lg text-rural-900">Profil Bisnis</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-rural-100 flex items-center justify-center text-rural-600 font-bold shrink-0">
                  {bp.business_name?.charAt(0) || 'P'}
                </div>
                <div>
                  <p className="font-bold text-slate-900 text-sm">{bp.business_name || '-'}</p>
                  <p className="text-xs text-slate-500 capitalize">{bp.business_type || '-'}</p>
                </div>
              </div>
              <div className="space-y-2 text-sm text-slate-600">
                <div className="flex justify-between">
                  <span className="text-slate-500">Pemilik</span>
                  <span className="font-medium">{user.full_name || user.email || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Email</span>
                  <span className="font-medium">{user.email || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Telepon</span>
                  <span className="font-medium">{bp.phone || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Alamat</span>
                  <span className="font-medium truncate max-w-[200px]">{bp.address || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Lokasi</span>
                  <span className="font-medium truncate max-w-[200px]">
                    {bp.village}, {bp.district}, {bp.city}, {bp.province}
                  </span>
                </div>
              </div>
            </CardBody>
          </Card>

          {/* Dokumen */}
          {verification.documents && verification.documents.length > 0 && (
            <Card className="mt-6">
              <CardHeader>
                <h2 className="font-bold text-lg text-slate-900">Dokumen Pendukung</h2>
              </CardHeader>
              <CardBody className="p-4 space-y-3">
                {verification.documents.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-500">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-900">{doc.document_type.toUpperCase()}</p>
                        <p className="text-xs text-slate-500">{formatDate(doc.uploaded_at)}</p>
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => downloadDocument(doc.id)}
                      className="text-rural-600 hover:text-rural-700"
                    >
                      <Download className="w-3 h-3 mr-1" /> Unduh
                    </Button>
                  </div>
                ))}
              </CardBody>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
