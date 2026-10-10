import { Users } from 'lucide-react'
import { Link } from 'react-router-dom'
import { AsyncBoundary, Card, PageHeader } from '../../components/ui'
import { useAuth } from '../../context/AuthContext'
import { useAsync } from '../../hooks/useAsync'
import { doctorService } from '../../services/adminService'

export default function DoctorDashboardPage() {
  const { user } = useAuth()
  const patients = useAsync(() => doctorService.patients(), [])
  return (
    <div>
      <PageHeader title={`Welcome, Dr. ${user.name}`} subtitle="Patients who have chosen to share their health summary with you." />
      <AsyncBoundary loading={patients.loading} error={patients.error} onRetry={patients.reload}>
        <Link to="/doctor/patients">
          <Card className="flex items-center gap-4 hover:border-brand-600">
            <Users className="size-12 text-brand-700" aria-hidden />
            <div><p className="text-4xl font-extrabold">{patients.data?.length ?? 0}</p><p className="text-slate-600">patients shared access with you</p></div>
          </Card>
        </Link>
        <p className="mt-4 text-slate-600">You see a patient only after they add your email in their profile. ArogyaAI does not provide clinical decision-making.</p>
      </AsyncBoundary>
    </div>
  )
}
