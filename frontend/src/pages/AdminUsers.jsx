import { useState, useEffect } from 'react'
import { adminService } from '../api/auth'
import { Card, CardBody } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { formatDate } from '../utils/format'
import { Users } from 'lucide-react'

export default function AdminUsers() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [updatingId, setUpdatingId] = useState(null)

  useEffect(() => {
    loadUsers()
  }, [search])

  const loadUsers = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = { page: 1, per_page: 50 }
      if (search.trim()) params.q = search.trim()
      const res = await adminService.getUsers(params)
      const data = res.data?.data || {}
      setUsers(Array.isArray(data.items) ? data.items : [])
    } catch (err) {
      console.error('Gagal memuat pengguna:', err)
      setError(err.response?.data?.message || 'Gagal memuat pengguna')
    } finally {
      setLoading(false)
    }
  }

  const updateUser = async (userId, payload) => {
    if (updatingId) return
    setUpdatingId(userId)
    try {
      await adminService.updateUser(userId, payload)
      await loadUsers()
    } catch (err) {
      alert(err.response?.data?.message || 'Gagal memperbarui pengguna')
    } finally {
      setUpdatingId(null)
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-rural-600"></div>
          <span className="text-sm text-slate-500">Memuat pengguna...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3 mb-6">
        <div>
          <h1 className="font-display font-bold text-2xl text-slate-900">Manajemen Pengguna</h1>
          <p className="text-slate-600 text-sm">
            Kelola status akun dan kemampuan beli/jual. Perubahan langsung berlaku.
          </p>
        </div>
        <input
          type="text"
          placeholder="Cari nama / email / bisnis..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border border-slate-200 rounded-xl px-4 py-2 text-sm focus:ring-2 focus:ring-rural-500 outline-none"
        />
      </div>

      {error && (
        <Card className="p-6 mb-6 border-red-100 bg-red-50">
          <p className="text-sm text-red-700">{error}</p>
        </Card>
      )}

      {users.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4 text-slate-400">
            <Users className="w-8 h-8" />
          </div>
          <h3 className="font-bold text-slate-900 mb-2">Tidak ada pengguna</h3>
          <p className="text-slate-500">Coba ubah kata kunci pencarian.</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {users.map((u) => (
            <Card key={u.id}>
              <CardBody className="p-4 flex flex-col lg:flex-row lg:items-center gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-bold text-slate-900 text-sm">
                      #{u.id} {u.full_name}
                    </p>
                    <Badge variant={u.role === 'admin' ? 'danger' : 'default'} className="text-[10px]">
                      {u.role}
                    </Badge>
                    <Badge
                      variant={u.account_status === 'active' ? 'success' : 'warning'}
                      className="text-[10px] capitalize"
                    >
                      {u.account_status}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-500 truncate">{u.email}</p>
                  {u.has_profile && u.business_profile && (
                    <p className="text-[11px] text-slate-400 truncate">
                      {u.business_profile.business_name} · dibuat {formatDate(u.created_at)}
                    </p>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-2 shrink-0">
                  {u.has_profile && u.business_profile ? (
                    <>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={updatingId === u.id}
                        onClick={() =>
                          updateUser(u.id, {
                            can_buy: !u.business_profile.can_buy,
                          })
                        }
                        className={`${
                          u.business_profile.can_buy
                            ? 'border-slate-300 text-slate-600'
                            : 'border-rural-300 text-rural-600 bg-rural-50'
                        }`}
                      >
                        Beli: {u.business_profile.can_buy ? 'ON' : 'OFF'}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={updatingId === u.id}
                        onClick={() =>
                          updateUser(u.id, {
                            can_sell: !u.business_profile.can_sell,
                          })
                        }
                        className={`${
                          u.business_profile.can_sell
                            ? 'border-slate-300 text-slate-600'
                            : 'border-rural-300 text-rural-600 bg-rural-50'
                        }`}
                      >
                        Jual: {u.business_profile.can_sell ? 'ON' : 'OFF'}
                      </Button>
                    </>
                  ) : (
                    <span className="text-[11px] text-slate-400">tanpa profil bisnis</span>
                  )}
                  {u.role !== 'admin' && (
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={updatingId === u.id}
                      onClick={() =>
                        updateUser(u.id, {
                          account_status:
                            u.account_status === 'active' ? 'suspended' : 'active',
                        })
                      }
                      className={`${
                        u.account_status === 'active'
                          ? 'border-slate-300 text-slate-600'
                          : 'border-rural-300 text-rural-600 bg-rural-50'
                      }`}
                    >
                      {u.account_status === 'active' ? 'Suspend' : 'Aktifkan'}
                    </Button>
                  )}
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
