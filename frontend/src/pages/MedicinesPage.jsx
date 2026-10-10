import { BellPlus, Check, Pencil, Pill, Plus, Trash2, X } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import Disclaimer from '../components/Disclaimer'
import { Alert, AsyncBoundary, Button, Card, EmptyState, Field, PageHeader, inputClass } from '../components/ui'
import { WEEKDAYS } from '../constants'
import { useLanguage } from '../context/LanguageContext'
import { useAsync } from '../hooks/useAsync'
import { medicineService } from '../services/medicineService'
import { getErrorMessage, getFieldErrors } from '../utils/errors'
import { formatDateTime, formatTime } from '../utils/format'

function MedicineForm({ initial, onSubmit, onCancel }) {
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm({
    defaultValues: initial || { name: '', dosage: '', instructions: '', start_date: '', end_date: '', is_active: true },
  })
  const submit = async (values) => {
    const payload = { ...values, start_date: values.start_date || null, end_date: values.end_date || null }
    try { await onSubmit(payload) } catch (error) {
      const fields = getFieldErrors(error)
      const known = Object.keys(fields).filter((key) => key in payload)
      known.forEach((key) => setError(key, { message: fields[key] }))
      if (!known.length) setError('root', { message: getErrorMessage(error) })
    }
  }
  return (
    <Card className="mb-6">
      <h2 className="mb-4 text-xl font-bold">{initial ? 'Edit medicine' : 'Add a medicine'}</h2>
      <p className="mb-4 text-sm text-slate-600">Enter the medicine exactly as your doctor or the label says. ArogyaAI does not choose doses for you.</p>
      <form onSubmit={handleSubmit(submit)} className="grid gap-4 sm:grid-cols-2" noValidate>
        {errors.root && <div className="sm:col-span-2"><Alert tone="error">{errors.root.message}</Alert></div>}
        <Field id="m-name" label="Medicine name" error={errors.name?.message}>
          <input id="m-name" className={inputClass} {...register('name', { required: 'Name is required.' })} />
        </Field>
        <Field id="m-dosage" label="Dose (as written on label)" error={errors.dosage?.message}>
          <input id="m-dosage" className={inputClass} placeholder="e.g. 1 tablet" {...register('dosage')} />
        </Field>
        <div className="sm:col-span-2">
          <Field id="m-instr" label="Instructions" error={errors.instructions?.message}>
            <textarea id="m-instr" rows={2} className={inputClass} placeholder="e.g. after food" {...register('instructions')} />
          </Field>
        </div>
        <Field id="m-start" label="Start date" error={errors.start_date?.message}><input id="m-start" type="date" className={inputClass} {...register('start_date')} /></Field>
        <Field id="m-end" label="End date" error={errors.end_date?.message}><input id="m-end" type="date" className={inputClass} {...register('end_date')} /></Field>
        <label className="flex items-center gap-2 font-semibold sm:col-span-2"><input type="checkbox" className="size-5" {...register('is_active')} /> Currently taking</label>
        <div className="flex gap-3 sm:col-span-2">
          <Button type="submit" loading={isSubmitting}>Save</Button>
          <Button variant="ghost" onClick={onCancel}>Cancel</Button>
        </div>
      </form>
    </Card>
  )
}

function ReminderForm({ onSubmit, onCancel }) {
  const { language } = useLanguage()
  const [time, setTime] = useState('08:00')
  const [days, setDays] = useState([])
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const toggle = (day) => setDays((current) => (current.includes(day) ? current.filter((d) => d !== day) : [...current, day]))
  const submit = async (event) => {
    event.preventDefault()
    setSaving(true); setError('')
    try { await onSubmit({ reminder_time: time, days_of_week: days }) } catch (err) { setError(getErrorMessage(err)) } finally { setSaving(false) }
  }
  return (
    <form onSubmit={submit} className="mt-3 space-y-3 rounded-xl bg-slate-50 p-3">
      {error && <Alert tone="error">{error}</Alert>}
      <Field id="r-time" label="Time"><input id="r-time" type="time" required value={time} onChange={(e) => setTime(e.target.value)} className={inputClass} /></Field>
      <fieldset>
        <legend className="mb-1 font-semibold">Days <span className="font-normal text-slate-600">(none selected = every day)</span></legend>
        <div className="flex flex-wrap gap-2">
          {WEEKDAYS.map((day) => (
            <button type="button" key={day.value} aria-pressed={days.includes(day.value)} onClick={() => toggle(day.value)}
              className={`min-h-11 min-w-14 rounded-xl border-2 px-3 font-semibold ${days.includes(day.value) ? 'border-brand-700 bg-brand-700 text-white' : 'border-slate-300 bg-white'}`}>
              {language === 'hi' ? day.hi : day.en}
            </button>
          ))}
        </div>
      </fieldset>
      <div className="flex gap-2"><Button type="submit" loading={saving}>Add reminder</Button><Button variant="ghost" onClick={onCancel}>Cancel</Button></div>
    </form>
  )
}

function MedicineCard({ medicine, onEdit, onChanged, onError }) {
  const { language } = useLanguage()
  const [showReminderForm, setShowReminderForm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [lastTaken, setLastTaken] = useState('')

  const run = async (action) => {
    setBusy(true)
    try { await action() } catch (err) { onError(getErrorMessage(err)) } finally { setBusy(false) }
  }
  const markTaken = () => run(async () => {
    const log = await medicineService.markTaken(medicine.id)
    setLastTaken(formatDateTime(log.taken_at))
  })
  const dayLabel = (code) => WEEKDAYS.find((d) => d.value === code)?.[language === 'hi' ? 'hi' : 'en'] || code

  return (
    <Card>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold">{medicine.name} {!medicine.is_active && <span className="ml-2 rounded-full bg-slate-200 px-2 py-0.5 align-middle text-sm font-semibold">Stopped</span>}</h2>
          {medicine.dosage && <p className="font-semibold text-slate-700">{medicine.dosage}</p>}
          {medicine.instructions && <p className="text-slate-600">{medicine.instructions}</p>}
        </div>
        <div className="flex gap-1">
          <button className="p-2" onClick={() => onEdit(medicine)} aria-label={`Edit ${medicine.name}`}><Pencil className="size-5" /></button>
          <button className="p-2 text-red-600" aria-label={`Delete ${medicine.name}`} disabled={busy}
            onClick={() => window.confirm(`Delete ${medicine.name}?`) && run(async () => { await medicineService.remove(medicine.id); onChanged() })}><Trash2 className="size-5" /></button>
        </div>
      </div>

      <ul className="mt-3 flex flex-wrap gap-2">
        {medicine.reminders?.map((reminder) => (
          <li key={reminder.id} className="flex items-center gap-1 rounded-full bg-brand-50 py-1 pl-3 pr-1 text-sm font-semibold text-brand-800">
            {formatTime(reminder.reminder_time)}{reminder.days_of_week?.length ? ` · ${reminder.days_of_week.map(dayLabel).join(', ')}` : ' · every day'}
            <button className="rounded-full p-1.5 hover:bg-brand-100" aria-label="Remove reminder"
              onClick={() => run(async () => { await medicineService.removeReminder(medicine.id, reminder.id); onChanged() })}><X className="size-4" /></button>
          </li>
        ))}
      </ul>

      {showReminderForm && (
        <ReminderForm onCancel={() => setShowReminderForm(false)}
          onSubmit={async (payload) => { await medicineService.addReminder(medicine.id, payload); setShowReminderForm(false); onChanged() }} />
      )}

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <Button onClick={markTaken} loading={busy} disabled={!medicine.is_active}><Check className="size-5" aria-hidden /> Mark as taken</Button>
        <Button variant="secondary" onClick={() => setShowReminderForm(true)}><BellPlus className="size-5" aria-hidden /> Add reminder time</Button>
        {lastTaken && <span className="text-sm font-semibold text-emerald-800">Logged {lastTaken}</span>}
      </div>
    </Card>
  )
}

export default function MedicinesPage() {
  const medicines = useAsync(() => medicineService.list(), [])
  const [editing, setEditing] = useState(null) // null | 'new' | medicine
  const [error, setError] = useState('')

  const save = async (payload) => {
    if (editing === 'new') await medicineService.create(payload)
    else await medicineService.update(editing.id, payload)
    setEditing(null)
    medicines.reload()
  }

  return (
    <div>
      <PageHeader title="My medicines" subtitle="Keep track of your medicines and the times to take them."
        action={!editing && <Button onClick={() => setEditing('new')}><Plus className="size-5" aria-hidden /> Add medicine</Button>} />
      <Alert tone="info" className="mb-6">Reminder times are saved here and shown on your home screen. ArogyaAI does not send phone alarms, SMS or notifications yet, so please also set an alarm on your phone.</Alert>
      {error && <Alert tone="error" className="mb-4">{error}</Alert>}
      {editing && <MedicineForm initial={editing === 'new' ? null : editing} onSubmit={save} onCancel={() => setEditing(null)} />}
      <AsyncBoundary loading={medicines.loading} error={medicines.error} onRetry={medicines.reload}>
        {medicines.data?.length ? (
          <div className="space-y-4">
            {medicines.data.map((medicine) => (
              <MedicineCard key={medicine.id} medicine={medicine} onEdit={setEditing} onChanged={medicines.reload} onError={setError} />
            ))}
          </div>
        ) : !editing && <EmptyState icon={Pill} title="No medicines added">Add a medicine to start tracking it.</EmptyState>}
      </AsyncBoundary>
      <Disclaimer className="mt-6" text="This list is only for your own tracking. Never start, stop or change a medicine without asking your doctor or pharmacist." />
    </div>
  )
}
