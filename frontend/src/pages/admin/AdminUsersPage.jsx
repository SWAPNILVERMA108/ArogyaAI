import { useState } from 'react'
import { Alert, AsyncBoundary, Card, PageHeader, inputClass } from '../../components/ui'
import { useAuth } from '../../context/AuthContext'
import { useAsync } from '../../hooks/useAsync'
import { adminService } from '../../services/adminService'
import { getErrorMessage } from '../../utils/errors'

export default function AdminUsersPage() {
  const { user: me } = useAuth()
  const [search, setSearch] = useState('')
  const [role, setRole] = useState('')
  const [error, setError] = useState('')
  const users = useAsync(() => adminService.users({ ...(search ? { search } : {}), ...(role ? { role } : {}) }), [search, role])

  const update = async (target, changes) => {
    setError('')
    try {
      const updated = await adminService.updateUser(target.id, changes)
      users.setData((current) => current.map((u) => (u.id === updated.id ? updated : u)))
    } catch (err) { setError(getErrorMessage(err)) }
  }

  return (
    <div>
      <PageHeader title="Users" subtitle="Promote trusted people to Doctor, or deactivate accounts." />
      <div className="mb-4 flex flex-wrap gap-3">
        <input aria-label="Search users" placeholder="Search name or email" className={`${inputClass} max-w-xs`} value={search} onChange={(e) => setSearch(e.target.value)} />
        <select aria-label="Filter by role" className={`${inputClass} max-w-48`} value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="">All roles</option><option value="PATIENT">Patients</option><option value="DOCTOR">Doctors</option><option value="ADMIN">Admins</option>
        </select>
      </div>
      {error && <Alert tone="error" className="mb-4">{error}</Alert>}
      <AsyncBoundary loading={users.loading && !users.data} error={users.error} onRetry={users.reload}>
        <Card className="overflow-x-auto p-0">
          <table className="w-full min-w-[40rem] text-left">
            <thead className="bg-slate-100 text-sm"><tr><th className="p-3">Name</th><th className="p-3">Email</th><th className="p-3">Role</th><th className="p-3">Active</th></tr></thead>
            <tbody>
              {users.data?.map((u) => {
                const isSelf = u.id === me.id
                return (
                  <tr key={u.id} className="border-t border-slate-100">
                    <td className="p-3 font-semibold">{u.name}</td><td className="p-3">{u.email}</td>
                    <td className="p-3">
                      <select aria-label={`Role for ${u.name}`} disabled={isSelf} value={u.role} onChange={(e) => update(u, { role: e.target.value })} className="min-h-10 rounded-lg border-2 border-slate-300 px-2">
                        <option value="PATIENT">Patient</option><option value="DOCTOR">Doctor</option><option value="ADMIN">Admin</option>
                      </select>
                    </td>
                    <td className="p-3"><input type="checkbox" className="size-6" aria-label={`Active: ${u.name}`} disabled={isSelf} checked={u.is_active} onChange={(e) => update(u, { is_active: e.target.checked })} /></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {users.data?.length === 0 && <p className="p-4 text-slate-600">No users match.</p>}
        </Card>
      </AsyncBoundary>
    </div>
  )
}
