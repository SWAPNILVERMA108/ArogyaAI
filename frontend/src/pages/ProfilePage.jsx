import { Trash2, UserPlus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { Alert, AsyncBoundary, Button, Card, Field, PageHeader, inputClass } from '../components/ui'
import { BLOOD_GROUPS, GENDERS, ROLES } from '../constants'
import { useAuth } from '../context/AuthContext'
import { useAsync } from '../hooks/useAsync'
import { authService } from '../services/authService'
import { patientService } from '../services/patientService'
import { getErrorMessage, getFieldErrors } from '../utils/errors'

function AccountForm() {
  const { user, setUser } = useAuth()
  const [message, setMessage] = useState({ tone: '', text: '' })
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm({
    defaultValues: { name: user.name, email: user.email, phone: user.phone },
  })
  const submit = async (values) => {
    setMessage({ tone: '', text: '' })
    try {
      setUser(await authService.updateProfile(values))
      setMessage({ tone: 'success', text: 'Account details saved.' })
    } catch (error) {
      const fields = getFieldErrors(error)
      const known = ['name', 'email', 'phone'].filter((key) => fields[key])
      known.forEach((key) => setError(key, { message: fields[key] }))
      if (!known.length) setMessage({ tone: 'error', text: getErrorMessage(error) })
    }
  }
  return (
    <Card>
      <h2 className="mb-4 text-xl font-bold">Account</h2>
      <form onSubmit={handleSubmit(submit)} className="grid gap-4 sm:grid-cols-2" noValidate>
        {message.text && <div className="sm:col-span-2"><Alert tone={message.tone}>{message.text}</Alert></div>}
        <Field id="a-name" label="Full name" error={errors.name?.message}><input id="a-name" className={inputClass} {...register('name', { required: 'Name is required.' })} /></Field>
        <Field id="a-email" label="Email" error={errors.email?.message}><input id="a-email" type="email" className={inputClass} {...register('email', { required: 'Email is required.' })} /></Field>
        <Field id="a-phone" label="Phone" error={errors.phone?.message}><input id="a-phone" type="tel" className={inputClass} {...register('phone')} /></Field>
        <div className="self-end"><Button type="submit" loading={isSubmitting}>Save</Button></div>
      </form>
    </Card>
  )
}

function HealthProfileForm({ profile, onSaved }) {
  const [message, setMessage] = useState({ tone: '', text: '' })
  const { register, handleSubmit, reset, setError, formState: { errors, isSubmitting } } = useForm()
  useEffect(() => {
    reset({
      date_of_birth: profile?.date_of_birth || '', gender: profile?.gender || '', blood_group: profile?.blood_group || '',
      height_cm: profile?.height_cm || '', weight_kg: profile?.weight_kg || '', allergies: profile?.allergies || '',
      medical_history: profile?.medical_history || '', emergency_contact: profile?.emergency_contact || '',
    })
  }, [profile, reset])

  const submit = async (values) => {
    setMessage({ tone: '', text: '' })
    const payload = {
      ...values,
      date_of_birth: values.date_of_birth || null,
      height_cm: values.height_cm === '' ? null : values.height_cm,
      weight_kg: values.weight_kg === '' ? null : values.weight_kg,
    }
    try {
      const saved = profile ? await patientService.update(payload) : await patientService.create(payload)
      onSaved(saved)
      setMessage({ tone: 'success', text: 'Health profile saved.' })
    } catch (error) {
      const fields = getFieldErrors(error)
      const known = Object.keys(payload).filter((key) => fields[key])
      known.forEach((key) => setError(key, { message: fields[key] }))
      if (!known.length) setMessage({ tone: 'error', text: getErrorMessage(error) })
    }
  }

  return (
    <Card>
      <h2 className="mb-1 text-xl font-bold">Health profile</h2>
      <p className="mb-4 text-slate-600">{profile ? 'Only you, and doctors you allow below, can see this.' : 'You have not created a health profile yet.'}</p>
      <form onSubmit={handleSubmit(submit)} className="grid gap-4 sm:grid-cols-2" noValidate>
        {message.text && <div className="sm:col-span-2"><Alert tone={message.tone}>{message.text}</Alert></div>}
        <Field id="p-dob" label="Date of birth" error={errors.date_of_birth?.message}><input id="p-dob" type="date" className={inputClass} {...register('date_of_birth')} /></Field>
        <Field id="p-gender" label="Gender" error={errors.gender?.message}>
          <select id="p-gender" className={inputClass} {...register('gender')}><option value="">Select</option>{GENDERS.map((g) => <option key={g} value={g}>{g.replaceAll('_', ' ').toLowerCase()}</option>)}</select>
        </Field>
        <Field id="p-blood" label="Blood group" error={errors.blood_group?.message}>
          <select id="p-blood" className={inputClass} {...register('blood_group')}><option value="">Select</option>{BLOOD_GROUPS.map((g) => <option key={g} value={g}>{g}</option>)}</select>
        </Field>
        <Field id="p-emerg" label="Emergency contact" error={errors.emergency_contact?.message}><input id="p-emerg" className={inputClass} {...register('emergency_contact')} /></Field>
        <Field id="p-height" label="Height (cm)" error={errors.height_cm?.message}><input id="p-height" type="number" step="0.1" className={inputClass} {...register('height_cm')} /></Field>
        <Field id="p-weight" label="Weight (kg)" error={errors.weight_kg?.message}><input id="p-weight" type="number" step="0.1" className={inputClass} {...register('weight_kg')} /></Field>
        <div className="sm:col-span-2"><Field id="p-allergies" label="Allergies" error={errors.allergies?.message}><textarea id="p-allergies" rows={2} className={inputClass} {...register('allergies')} /></Field></div>
        <div className="sm:col-span-2"><Field id="p-history" label="Medical history" error={errors.medical_history?.message}><textarea id="p-history" rows={3} className={inputClass} {...register('medical_history')} /></Field></div>
        <div className="sm:col-span-2"><Button type="submit" loading={isSubmitting}>{profile ? 'Save changes' : 'Create profile'}</Button></div>
      </form>
    </Card>
  )
}

function DoctorAccess() {
  const grants = useAsync(() => patientService.listAccess(), [])
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState({ tone: '', text: '' })
  const [saving, setSaving] = useState(false)

  const grant = async (event) => {
    event.preventDefault()
    setSaving(true); setMessage({ tone: '', text: '' })
    try { await patientService.grantAccess(email.trim()); setEmail(''); grants.reload() } catch (err) { setMessage({ tone: 'error', text: getErrorMessage(err) }) } finally { setSaving(false) }
  }
  return (
    <Card>
      <h2 className="mb-1 text-xl font-bold">Doctors who can see my health summary</h2>
      <p className="mb-4 text-slate-600">A doctor can only see your profile and active medicines after you add their email here. You can remove access at any time.</p>
      <AsyncBoundary loading={grants.loading} error={grants.error} onRetry={grants.reload}>
        <ul className="mb-4 divide-y divide-slate-100">
          {grants.data?.map((item) => (
            <li key={item.id} className="flex items-center justify-between py-2">
              <span><strong>{item.doctor_name}</strong> <span className="text-slate-600">{item.doctor_email}</span></span>
              <button className="p-2 text-red-600" aria-label={`Remove access for ${item.doctor_name}`}
                onClick={async () => { try { await patientService.revokeAccess(item.id); grants.reload() } catch (err) { setMessage({ tone: 'error', text: getErrorMessage(err) }) } }}><Trash2 /></button>
            </li>
          ))}
          {!grants.data?.length && <li className="py-2 text-slate-600">No doctor has access.</li>}
        </ul>
      </AsyncBoundary>
      {message.text && <Alert tone={message.tone} className="mb-3">{message.text}</Alert>}
      <form onSubmit={grant} className="flex flex-wrap items-end gap-3">
        <div className="min-w-60 flex-1"><Field id="d-email" label="Doctor's email"><input id="d-email" type="email" required className={inputClass} value={email} onChange={(e) => setEmail(e.target.value)} /></Field></div>
        <Button type="submit" loading={saving}><UserPlus className="size-5" aria-hidden /> Allow access</Button>
      </form>
    </Card>
  )
}

export default function ProfilePage() {
  const { user } = useAuth()
  const isPatient = user.role === ROLES.PATIENT
  const profile = useAsync(() => (isPatient ? patientService.getMine() : Promise.resolve(null)), [isPatient])

  return (
    <div className="space-y-6">
      <PageHeader title="My profile" subtitle={`Signed in as ${user.role.toLowerCase()}`} />
      <AccountForm />
      {isPatient && (
        <AsyncBoundary loading={profile.loading} error={profile.error} onRetry={profile.reload}>
          <HealthProfileForm profile={profile.data} onSaved={profile.setData} />
          <DoctorAccess />
        </AsyncBoundary>
      )}
    </div>
  )
}
