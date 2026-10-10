import { Users } from 'lucide-react'
import { useState } from 'react'
import { AsyncBoundary, Button, Card, EmptyState, PageHeader } from '../../components/ui'
import { useAsync } from '../../hooks/useAsync'
import { doctorService } from '../../services/adminService'
import { formatDate } from '../../utils/format'

function PatientDetail({ id, onClose }) {
  const detail = useAsync(() => doctorService.patient(id), [id])
  const patient = detail.data
  const profile = patient?.profile
  return (
    <Card className="mb-6 border-2 border-brand-600">
      <div className="mb-3 flex items-center justify-between"><h2 className="text-xl font-bold">Patient summary</h2><Button variant="ghost" onClick={onClose}>Close</Button></div>
      <AsyncBoundary loading={detail.loading} error={detail.error} onRetry={detail.reload}>
        {patient && (
          <div className="space-y-3">
            <p className="text-lg font-bold">{patient.name} <span className="font-normal text-slate-600">{patient.email}{patient.phone && ` · ${patient.phone}`}</span></p>
            {profile ? (
              <dl className="grid gap-x-6 gap-y-2 sm:grid-cols-2">
                {[['Age', profile.age], ['Gender', profile.gender], ['Blood group', profile.blood_group], ['Height (cm)', profile.height_cm], ['Weight (kg)', profile.weight_kg], ['Emergency contact', profile.emergency_contact], ['Allergies', profile.allergies], ['Medical history', profile.medical_history]].map(([label, value]) => (
                  <div key={label}><dt className="text-sm font-semibold text-slate-500">{label}</dt><dd className="whitespace-pre-wrap">{value || '—'}</dd></div>
                ))}
              </dl>
            ) : <p className="text-slate-600">This patient has not created a health profile.</p>}
            <div>
              <h3 className="font-bold">Current medicines</h3>
              {patient.medicines.length ? (
                <ul className="list-disc pl-6">{patient.medicines.map((m) => <li key={m.id}>{m.name}{m.dosage && ` — ${m.dosage}`}{m.instructions && ` (${m.instructions})`}</li>)}</ul>
              ) : <p className="text-slate-600">None recorded.</p>}
            </div>
          </div>
        )}
      </AsyncBoundary>
    </Card>
  )
}

export default function DoctorPatientsPage() {
  const patients = useAsync(() => doctorService.patients(), [])
  const [selected, setSelected] = useState(null)
  return (
    <div>
      <PageHeader title="My patients" subtitle="Only patients who granted you access appear here." />
      {selected && <PatientDetail id={selected} onClose={() => setSelected(null)} />}
      <AsyncBoundary loading={patients.loading} error={patients.error} onRetry={patients.reload}>
        {patients.data?.length ? (
          <ul className="space-y-3">
            {patients.data.map((p) => (
              <li key={p.patient_id}>
                <Card className="flex flex-wrap items-center justify-between gap-3">
                  <div><p className="text-lg font-bold">{p.name}</p><p className="text-slate-600">{p.email} · access since {formatDate(p.granted_at)}</p></div>
                  <Button variant="secondary" onClick={() => setSelected(p.patient_id)}>View summary</Button>
                </Card>
              </li>
            ))}
          </ul>
        ) : <EmptyState icon={Users} title="No patients yet">Patients can add your email under Profile → Doctors who can see my health summary.</EmptyState>}
      </AsyncBoundary>
    </div>
  )
}
