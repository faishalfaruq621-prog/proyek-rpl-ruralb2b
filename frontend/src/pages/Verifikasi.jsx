import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { businessProfileService } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { Card } from '../components/ui/Card'
import { CardHeader } from '../components/ui/Card'
import { CardBody } from '../components/ui/Card'
import { CardFooter } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Upload, FileText, Clock, ShieldCheck, AlertTriangle } from 'lucide-react'

const DOCUMENT_TYPES = [
  { value: 'ktp', label: 'KTP' },
  { value: 'kk', label: 'Kartu Keluarga (KK)' },
  { value: 'npwp', label: 'NPWP' },
  { value: 'nib', label: 'NIB' },
  { value: 'siup', label: 'SIUP' },
  { value: 'business_photo', label: 'Foto Usaha' },
  { value: 'other', label: 'Lainnya' },
]

export default function Verifikasi() {
  const { user } = useAuth()
  const { success, error } = useToast()
  const navigate = useNavigate()

  const [profile, setProfile] = useState(null)
  const [verification, setVerification] = useState(null)
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [selectedDocType, setSelectedDocType] = useState('ktp')
  const [proofFile, setProofFile] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const res = await businessProfileService.getProfile()
      const data = res.data.data || res.data
      setProfile(data.profile || data)
      setVerification(data.verification || null)
    } catch (err) {
      error('Gagal memuat data verifikasi: ' + (err.response?.data?.message || err.message))
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitVerification = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const res = await businessProfileService.submitVerification({})
      setVerification(res.data.data.verification || res.data.data)
      success('Pengajuan verifikasi berhasil dibuat. Silakan unggah dokumen pendukung.')
    } catch (err) {
      error(err.response?.data?.message || 'Gagal mengajukan verifikasi')
    } finally {
      setSubmitting(false)
    }
  }

  const handleUploadDocument = async (e) => {
    e.preventDefault()
    if (!proofFile) {
      error('Pilih file terlebih dahulu.')
      return
    }
    setUploading(true)
    const formData = new FormData()
    formData.append('document_type', selectedDocType)
    formData.append('file', proofFile)
    try {
      const vid = verification?.id
      if (!vid) {
        error('Data verifikasi tidak ditemukan.')
        return
      }
      await businessProfileService.uploadDocument(vid, formData)
      setProofFile(null)
      setSelectedDocType('ktp')
      success('Dokumen berhasil diunggah.')
      loadData()
    } catch (err) {
      error(err.response?.data?.message || 'Gagal mengunggah dokumen')
    } finally {
      setUploading(false)
    }
  }

  const handleDownloadDocument = (docId) => {
    const vid = verification?.id
    if (!vid) return
    window.location.href = `/api/business/verifications/${vid}/documents/${docId}/download`
  }

  const isVerified = verification?.status === 'approved'
  const isPending = verification?.status === 'pending'
  const isRejected = verification?.status === 'rejected'

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
          <h1 className="font-display font-bold text-2xl text-slate-900">Verifikasi UMKM</h1>
          <p className="text-slate-600">
            Ajukan verifikasi bisnis untuk mendapatkan badge terverifikasi dan
            meningkatkan kepercayaan pembeli.
          </p>
        </div>
        <Link to="/profil-bisnis" className="text-sm text-rural-600 hover:text-rural-700">
          Kembali ke Profil Bisnis
        </Link>
      </div>

      {/* Status Verifikasi */}
      <Card className="mb-8">
        <CardHeader>
          <h2 className="font-bold text-lg text-slate-900">Status Verifikasi</h2>
        </CardHeader>
        <CardBody className="p-6">
          <div className="flex items-center gap-4 mb-6">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold ${
              isVerified ? 'bg-rural-600' : isPending ? 'bg-amber-500' : isRejected ? 'bg-red-500' : 'bg-slate-200'
            }`}>
              {isVerified ? <ShieldCheck className="w-6 h-6" /> : isPending ? <Clock className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
            </div>
            <div>
              <p className={`font-bold text-slate-900 ${isVerified ? 'text-rural-700' : isPending ? 'text-amber-800' : isRejected ? 'text-red-800' : 'text-slate-600'}`}>
                {isVerified ? 'Terverifikasi' : isPending ? 'Menunggu Verifikasi' : isRejected ? 'Ditolak' : 'Belum Ajukan'}
              </p>
              {verification?.rejection_reason && (
                <p className="text-xs text-red-600 mt-1">Alasan: {verification.rejection_reason}</p>
              )}
            </div>
          </div>

          {isVerified && (
            <div className="bg-rural-50 border border-rural-100 rounded-xl p-4">
              <div className="flex items-center gap-2 text-rural-700 text-sm font-medium mb-2">
                <ShieldCheck className="w-4 h-4" />
                <span>Bisnis Anda telah terverifikasi.</span>
              </div>
              <p className="text-xs text-rural-600">
                Badge terverifikasi akan ditampilkan di profil bisnis dan produk Anda.
              </p>
            </div>
          )}

          {!isVerified && !isPending && (
            <div className="bg-slate-50 border border-slate-100 rounded-xl p-4">
              <div className="flex items-center gap-2 text-slate-700 text-sm font-medium mb-2">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>Anda belum mengajukan verifikasi.</span>
              </div>
              <p className="text-xs text-slate-600">
                Ajukan verifikasi dan unggah dokumen pendukung (KTP, NPWP, NIB, dll.)
                untuk diajukan ke admin.
              </p>
            </div>
          )}

          {isPending && (
            <div className="bg-amber-50 border border-amber-100 rounded-xl p-4">
              <div className="flex items-center gap-2 text-amber-800 text-sm font-medium mb-2">
                <Clock className="w-4 h-4" />
                <span>Pengajuan Anda sedang menunggu verifikasi admin.</span>
              </div>
              <p className="text-xs text-amber-700">
                Silakan menunggu hingga admin meninjau dokumen Anda.
              </p>
            </div>
          )}
        </CardBody>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Ajukan Verifikasi */}
        {!isVerified && !isPending && (
          <Card>
            <CardHeader>
              <h2 className="font-bold text-lg text-slate-900">Ajukan Verifikasi</h2>
            </CardHeader>
            <CardBody>
              <form onSubmit={handleSubmitVerification} className="space-y-4">
                <p className="text-sm text-slate-600">
                  Mengajukan verifikasi akan membuat status pengajuan menjadi
                  <span className="font-medium text-amber-600">pending</span>.
                  Setelah itu, silakan unggah dokumen pendukung di bawah.
                </p>
                <Button
                  type="submit"
                  disabled={submitting}
                  className="w-full bg-rural-600 hover:bg-rural-700 text-white py-3"
                >
                  {submitting ? 'Mengajukan...' : 'Ajukan Verifikasi Sekarang'}
                </Button>
              </form>
            </CardBody>
          </Card>
        )}

        {/* Upload Dokumen */}
        {(isPending || isRejected) && (
          <Card>
            <CardHeader>
              <h2 className="font-bold text-lg text-slate-900">
                {isPending ? 'Unggah Dokumen Pendukung' : 'Unggah Ulang Dokumen'}
              </h2>
            </CardHeader>
            <CardBody>
              <form onSubmit={handleUploadDocument} className="space-y-4">
                <div>
                  <label className="label">Jenis Dokumen</label>
                  <select
                    value={selectedDocType}
                    onChange={(e) => setSelectedDocType(e.target.value)}
                    className="input"
                  >
                    {DOCUMENT_TYPES.map((dt) => (
                      <option key={dt.value} value={dt.value}>
                        {dt.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">Pilih File</label>
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png,.webp"
                    onChange={(e) => setProofFile(e.target.files?.[0] || null)}
                    className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-rural-50 file:text-rural-700 hover:file:bg-rural-100 cursor-pointer"
                  />
                  <p className="text-xs text-slate-400 mt-1">
                    PDF, JPG, JPEG, PNG, WEBP. Maksimal 5 MB per file.
                  </p>
                </div>
                <Button
                  type="submit"
                  disabled={uploading || !proofFile}
                  className="w-full bg-rural-600 hover:bg-rural-700 text-white py-3"
                >
                  {uploading ? 'Mengunggah...' : 'Unggah Dokumen'}
                </Button>
              </form>
            </CardBody>
          </Card>
        )}

        {/* Daftar Dokumen */}
        {documents.length > 0 && (
          <Card>
            <CardHeader>
              <h2 className="font-bold text-lg text-slate-900">Dokumen yang Diunggah</h2>
            </CardHeader>
            <CardBody className="p-4">
              <div className="space-y-3">
                {documents.map((doc) => (
                  <div key={doc.id} className="flex justify-between items-center p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-500">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-900">{doc.document_type.toUpperCase()}</p>
                        <p className="text-xs text-slate-500">{doc.uploaded_at || ''}</p>
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDownloadDocument(doc.id)}
                      className="text-rural-600 hover:text-rural-700"
                    >
                      <Upload className="w-3 h-3 mr-1" /> Unduh
                    </Button>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        )}
      </div>
    </div>
  )
}
