import { useState, useEffect, useCallback } from 'react'
import { adminService } from '../../api/auth'
import { Card, CardHeader, CardBody } from '../ui/Card'
import { Button } from '../ui/Button'
import { Badge } from '../ui/Badge'
import { useToast } from '../../context/ToastContext'
import { SendHorizonal, History, MessageSquareShare, RefreshCw } from 'lucide-react'

/**
 * Section "Preferensi Notifikasi — Integrasi Telegram" untuk profil Admin.
 * Hanya dirender untuk role admin (dikelola oleh pemanggil). Tidak ada menu
 * sidebar baru; halaman profil Buyer/Seller tidak diubah.
 */
export default function TelegramSettings() {
  const { error: toastError, success: toastSuccess } = useToast()
  const [status, setStatus] = useState(null)
  const [loadingStatus, setLoadingStatus] = useState(true)
  const [testing, setTesting] = useState(false)
  const [sending, setSending] = useState(false)
  const [logs, setLogs] = useState([])
  const [loadingLogs, setLoadingLogs] = useState(true)

  const loadStatus = useCallback(async () => {
    setLoadingStatus(true)
    try {
      const res = await adminService.getTelegramStatus()
      setStatus(res.data?.data || null)
    } catch (err) {
      toastError(
        err.response?.data?.message || 'Gagal memuat status Telegram.'
      )
    } finally {
      setLoadingStatus(false)
    }
  }, [toastError])

  const loadLogs = useCallback(async () => {
    setLoadingLogs(true)
    try {
      const res = await adminService.getTelegramLogs({ limit: 20 })
      setLogs(res.data?.data?.items || [])
    } catch (err) {
      // Riwayat gagal dimuat tidak boleh merusak halaman.
      setLogs([])
    } finally {
      setLoadingLogs(false)
    }
  }, [])

  useEffect(() => {
    loadStatus()
    loadLogs()
  }, [loadStatus, loadLogs])

  const statusBadge = () => {
    if (loadingStatus) return <Badge variant="default">Memeriksa...</Badge>
    if (!status) return <Badge variant="danger">Gangguan</Badge>
    if (status.connection === 'connected')
      return <Badge variant="success">Terhubung</Badge>
    if (status.connection === 'error')
      return <Badge variant="warning">Gangguan</Badge>
    return <Badge variant="danger">Tidak terhubung</Badge>
  }

  const handleTestConnection = async () => {
    if (testing) return
    setTesting(true)
    try {
      const res = await adminService.testTelegramConnection()
      const d = res.data?.data || {}
      if (d.ok) {
        toastSuccess(
          `Koneksi Telegram OK (bot @${d.bot_username}). Tidak ada pesan dikirim.`
        )
      } else {
        toastError(d.message || 'Koneksi Telegram gagal.')
      }
      loadStatus()
    } catch (err) {
      toastError(
        err.response?.data?.message || 'Gagal menguji koneksi Telegram.'
      )
    } finally {
      setTesting(false)
    }
  }

  const handleSendTestMessage = async () => {
    if (sending) return
    // Dialog konfirmasi wajib sebelum pengiriman (satu pesan, tanpa retry).
    const ok = window.confirm(
      'Kirim SATU pesan tes ke chat admin yang terkonfigurasi?\n\n' +
        'Pesan dikirim tepat satu kali (tanpa retry otomatis) menggunakan ' +
        'mekanisme notifikasi resmi sistem.'
    )
    if (!ok) return
    setSending(true)
    try {
      const res = await adminService.sendTelegramTestMessage()
      const d = res.data?.data || {}
      if (d.sent) {
        toastSuccess(
          `Pesan tes terkirim (message_id ${d.message_id}). Cek Telegram Anda.`
        )
      } else {
        toastError(d.message || 'Pengiriman pesan tes gagal.')
      }
      loadStatus()
      loadLogs()
    } catch (err) {
      toastError(
        err.response?.data?.message || 'Gagal mengirim pesan tes Telegram.'
      )
    } finally {
      setSending(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <h2 className="font-bold text-lg text-slate-900 flex items-center gap-2">
          <MessageSquareShare className="w-5 h-5 text-rural-600" />{' '}
          Preferensi Notifikasi — Integrasi Telegram
        </h2>
      </CardHeader>
      <CardBody className="p-5 space-y-5">
        {/* ===== Informasi integrasi ===== */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          <div className="flex justify-between gap-3 p-3 border border-slate-200 rounded-xl">
            <span className="text-slate-600 shrink-0">Nama Integrasi</span>
            <span className="font-medium text-slate-900 text-right">
              Telegram Notification
            </span>
          </div>
          <div className="flex justify-between gap-3 p-3 border border-slate-200 rounded-xl">
            <span className="text-slate-600 shrink-0">Nama Bot</span>
            <span className="font-medium text-slate-900 text-right">
              RuralB2B Notification
            </span>
          </div>
          <div className="flex justify-between gap-3 p-3 border border-slate-200 rounded-xl">
            <span className="text-slate-600 shrink-0">Username</span>
            <span className="font-medium text-slate-900 text-right">
              {loadingStatus
                ? '...'
                : status?.bot_username
                  ? `@${status.bot_username}`
                  : '@RuralB2B_Notification_bot'}
            </span>
          </div>
          <div className="flex justify-between gap-3 p-3 border border-slate-200 rounded-xl">
            <span className="text-slate-600 shrink-0">Chat ID</span>
            <span className="font-medium text-slate-900 text-right font-mono">
              {loadingStatus ? '...' : status?.chat_id_masked || '-'}
            </span>
          </div>
          <div className="flex justify-between gap-3 p-3 border border-slate-200 rounded-xl">
            <span className="text-slate-600 shrink-0">Status Koneksi</span>
            {statusBadge()}
          </div>
          <div className="flex justify-between gap-3 p-3 border border-slate-200 rounded-xl">
            <span className="text-slate-600 shrink-0">Jenis Integrasi</span>
            <span className="font-medium text-slate-900 text-right">
              Telegram Bot API
            </span>
          </div>
        </div>

        {status?.message && status.connection !== 'connected' && (
          <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3">
            {status.message}
          </p>
        )}

        {/* ===== Pengujian ===== */}
        <div className="flex flex-col sm:flex-row gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleTestConnection}
            disabled={testing}
            className="justify-center border border-slate-300 text-slate-700 hover:bg-slate-50"
          >
            <RefreshCw className={`w-4 h-4 ${testing ? 'animate-spin' : ''}`} />
            {testing ? 'Memeriksa...' : 'Tes Koneksi'}
          </Button>
          <Button
            size="sm"
            onClick={handleSendTestMessage}
            disabled={sending}
            className="justify-center bg-rural-600 hover:bg-rural-700 text-white"
          >
            <SendHorizonal className="w-4 h-4" />
            {sending ? 'Mengirim...' : 'Kirim Pesan Tes'}
          </Button>
        </div>
        <p className="text-xs text-slate-500">
          Tes koneksi hanya memeriksa Bot API (tidak mengirim pesan). Kirim
          pesan tes memerlukan konfirmasi dan mengirim tepat satu pesan.
        </p>

        {/* ===== Riwayat notifikasi ===== */}
        <div className="pt-2">
          <h3 className="font-semibold text-sm text-slate-900 flex items-center gap-2 mb-2">
            <History className="w-4 h-4 text-rural-600" /> Riwayat Notifikasi
          </h3>
          {loadingLogs ? (
            <p className="text-sm text-slate-500">Memuat riwayat...</p>
          ) : logs.length === 0 ? (
            <div className="text-sm text-slate-500 bg-slate-50 border border-slate-200 rounded-xl p-4 text-center">
              Belum ada notifikasi Telegram terkirim. Riwayat akan muncul di
              sini setelah ada notifikasi sistem (verifikasi bisnis) atau pesan
              tes yang dikirim.
            </div>
          ) : (
            <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className="flex flex-wrap items-center gap-2 px-4 py-3 text-sm"
                >
                  <span className="text-slate-500 text-xs font-mono shrink-0">
                    {log.created_at
                      ? new Date(log.created_at).toLocaleString('id-ID')
                      : '-'}
                  </span>
                  <span className="font-medium text-slate-900">
                    {log.jenis}
                  </span>
                  <Badge
                    variant={log.delivery_status === 'success' ? 'success' : 'danger'}
                    className="capitalize text-[10px]"
                  >
                    {log.delivery_status}
                  </Badge>
                  {log.error_message && (
                    <span className="text-xs text-red-600 truncate w-full sm:w-auto">
                      {log.error_message}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  )
}
