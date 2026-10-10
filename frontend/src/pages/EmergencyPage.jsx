import { Copy, MapPin, MessageSquareShare, Phone, Plus, Star, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { FacilityList } from '../components/FacilitySearch'
import { Alert, AsyncBoundary, Button, Card, Field, inputClass } from '../components/ui'
import { useGeolocation } from '../hooks/useGeolocation'
import { useAsync } from '../hooks/useAsync'
import { emergencyService } from '../services/emergencyService'
import { hospitalService } from '../services/hospitalService'
import { getErrorMessage, getFieldErrors } from '../utils/errors'

function ContactForm({ onSaved }) {
  const { register, handleSubmit, reset, setError, formState: { errors, isSubmitting } } = useForm({ defaultValues: { is_primary: false } })
  const submit = async (values) => {
    try { await emergencyService.createContact(values); reset(); onSaved() } catch (error) {
      const fields = getFieldErrors(error)
      const known = ['name', 'phone', 'relationship', 'is_primary'].filter((key) => fields[key])
      known.forEach((key) => setError(key, { message: fields[key] }))
      if (!known.length) setError('root', { message: getErrorMessage(error) })
    }
  }
  return (
    <form onSubmit={handleSubmit(submit)} className="mt-4 grid gap-3 rounded-xl bg-slate-50 p-4 sm:grid-cols-2" noValidate>
      {errors.root && <div className="sm:col-span-2"><Alert tone="error">{errors.root.message}</Alert></div>}
      <Field id="c-name" label="Name" error={errors.name?.message}><input id="c-name" className={inputClass} {...register('name', { required: 'Name is required.' })} /></Field>
      <Field id="c-phone" label="Phone" error={errors.phone?.message}><input id="c-phone" type="tel" className={inputClass} {...register('phone', { required: 'Phone is required.' })} /></Field>
      <Field id="c-rel" label="Relationship" error={errors.relationship?.message}><input id="c-rel" className={inputClass} placeholder="e.g. Son" {...register('relationship')} /></Field>
      <label className="flex items-center gap-2 self-end pb-3 font-semibold"><input type="checkbox" className="size-5" {...register('is_primary')} /> Main contact</label>
      <div className="sm:col-span-2"><Button type="submit" loading={isSubmitting}><Plus className="size-5" aria-hidden /> Save contact</Button></div>
    </form>
  )
}

export default function EmergencyPage() {
  const info = useAsync(() => emergencyService.info(), [])
  const contacts = useAsync(() => emergencyService.listContacts(), [])
  const { locate, locating } = useGeolocation()
  const [error, setError] = useState('')
  const [share, setShare] = useState(null)
  const [nearby, setNearby] = useState(null)
  const [busy, setBusy] = useState('')
  const [copied, setCopied] = useState(false)

  const prepareShare = async (contactId) => {
    setError(''); setBusy('share'); setCopied(false)
    try {
      const { latitude, longitude } = await locate()
      setShare(await emergencyService.shareLocation({ latitude, longitude, contactId }))
    } catch (err) { setError(err.response ? getErrorMessage(err) : err.message) } finally { setBusy('') }
  }

  const findEmergencyFacilities = async () => {
    setError(''); setBusy('nearby')
    try {
      const { latitude, longitude } = await locate()
      setNearby(await hospitalService.nearby({ latitude, longitude, radius: 10000, category: 'emergency' }))
    } catch (err) { setError(err.response ? getErrorMessage(err) : err.message) } finally { setBusy('') }
  }

  const copy = async () => {
    try { await navigator.clipboard.writeText(share.message); setCopied(true) } catch { setError('Could not copy. Please select and copy the message manually.') }
  }

  return (
    <div className="space-y-6">
      <AsyncBoundary loading={info.loading} error={info.error} onRetry={info.reload}>
        {info.data && (
          <Card className="border-2 border-red-300 bg-red-50 text-center">
            <h1 className="text-2xl font-bold text-red-800">Emergency</h1>
            <p className="mt-1 text-red-900">If someone is in danger, call now. Do not wait for the app.</p>
            {info.data.call_uri ? (
              <a href={info.data.call_uri} className="mx-auto mt-4 flex min-h-20 max-w-md items-center justify-center gap-3 rounded-2xl bg-red-600 px-6 text-2xl font-extrabold text-white hover:bg-red-700">
                <Phone className="size-8" aria-hidden /> Call {info.data.emergency_number}
              </a>
            ) : <Alert tone="warning" className="mt-4">No emergency number is configured. Dial your local emergency number.</Alert>}
            <p className="mt-2 font-semibold">{info.data.emergency_label}</p>
            <p className="mx-auto mt-3 max-w-xl text-sm text-red-900">{info.data.disclaimer}</p>
            <ul className="mx-auto mt-4 max-w-xl list-disc space-y-1 pl-6 text-left text-red-950">
              {info.data.guidance.map((line) => <li key={line}>{line}</li>)}
            </ul>
          </Card>
        )}
      </AsyncBoundary>

      {error && <Alert tone="error">{error}</Alert>}

      <Card>
        <h2 className="text-xl font-bold">Share my location</h2>
        <p className="text-slate-600">We prepare a message with a map link for you to review. Nothing is sent automatically and your location is not saved.</p>
        <Button className="mt-3" variant="secondary" loading={busy === 'share' || locating} onClick={() => prepareShare()}><MapPin className="size-5" aria-hidden /> Prepare location message</Button>
        {share && (
          <div className="mt-4 space-y-3 rounded-xl bg-slate-50 p-4">
            <p className="whitespace-pre-wrap break-words font-semibold">{share.message}</p>
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" onClick={copy}><Copy className="size-5" aria-hidden /> {copied ? 'Copied' : 'Copy message'}</Button>
              <a className="inline-flex min-h-12 items-center gap-2 rounded-xl bg-brand-700 px-5 font-semibold text-white" href={`sms:${share.contact?.phone || ''}?body=${encodeURIComponent(share.message)}`}><MessageSquareShare className="size-5" aria-hidden /> Open SMS</a>
              <a className="inline-flex min-h-12 items-center gap-2 rounded-xl border-2 border-brand-700 px-5 font-semibold text-brand-800" href={`https://wa.me/?text=${encodeURIComponent(share.message)}`} target="_blank" rel="noreferrer">WhatsApp</a>
            </div>
            <p className="text-sm text-slate-600">{share.notice}</p>
          </div>
        )}
      </Card>

      <Card>
        <h2 className="text-xl font-bold">My emergency contacts</h2>
        <AsyncBoundary loading={contacts.loading} error={contacts.error} onRetry={contacts.reload}>
          <ul className="mt-3 divide-y divide-slate-100">
            {contacts.data?.map((contact) => (
              <li key={contact.id} className="flex flex-wrap items-center justify-between gap-2 py-3">
                <div>
                  <p className="font-bold">{contact.name} {contact.is_primary && <Star className="inline size-4 fill-amber-400 text-amber-500" aria-label="Main contact" />}</p>
                  <p className="text-slate-600">{contact.phone}{contact.relationship && ` · ${contact.relationship}`}</p>
                </div>
                <div className="flex gap-2">
                  <a href={`tel:${contact.phone.replace(/[^0-9+]/g, '')}`} className="inline-flex min-h-11 items-center gap-1 rounded-xl bg-brand-700 px-4 font-semibold text-white"><Phone className="size-4" aria-hidden /> Call</a>
                  <Button variant="secondary" className="min-h-11" onClick={() => prepareShare(contact.id)}>Share location</Button>
                  <button className="p-2 text-red-600" aria-label={`Delete ${contact.name}`}
                    onClick={async () => { if (window.confirm(`Delete ${contact.name}?`)) { try { await emergencyService.deleteContact(contact.id); contacts.reload() } catch (err) { setError(getErrorMessage(err)) } } }}><Trash2 /></button>
                </div>
              </li>
            ))}
            {!contacts.data?.length && <li className="py-3 text-slate-600">No contacts yet. Add someone who should be told when you need help.</li>}
          </ul>
          <ContactForm onSaved={contacts.reload} />
        </AsyncBoundary>
      </Card>

      <Card>
        <h2 className="text-xl font-bold">Nearby emergency facilities</h2>
        <Button className="mt-3" variant="secondary" loading={busy === 'nearby' || locating} onClick={findEmergencyFacilities}>Find near me</Button>
        <FacilityList result={nearby} />
      </Card>
    </div>
  )
}
