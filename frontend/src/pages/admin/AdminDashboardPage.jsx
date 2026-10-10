import { AsyncBoundary, Card, PageHeader } from '../../components/ui'
import { useAsync } from '../../hooks/useAsync'
import { adminService } from '../../services/adminService'

export default function AdminDashboardPage() {
  const stats = useAsync(() => adminService.stats(), [])
  const s = stats.data
  const tiles = s && [
    ['Users', s.users_total], ['Patients', s.users_by_role.PATIENT], ['Doctors', s.users_by_role.DOCTOR],
    ['Admins', s.users_by_role.ADMIN], ['Inactive accounts', s.inactive_users], ['Conversations', s.conversations],
    ['Reports uploaded', s.reports], ['Medicines tracked', s.medicines],
  ]
  return (
    <div>
      <PageHeader title="Admin dashboard" subtitle="Platform totals. Private health content is not shown here." />
      <AsyncBoundary loading={stats.loading} error={stats.error} onRetry={stats.reload}>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {tiles?.map(([label, value]) => <Card key={label}><p className="text-3xl font-extrabold">{value}</p><p className="text-slate-600">{label}</p></Card>)}
        </div>
      </AsyncBoundary>
    </div>
  )
}
