import { ExternalLink, LocateFixed, Phone, Search } from 'lucide-react'
import { useState } from 'react'
import { Alert, Button, Card, EmptyState, Field, inputClass } from './ui'
import { FACILITY_CATEGORIES } from '../constants'
import { useGeolocation } from '../hooks/useGeolocation'
import { hospitalService } from '../services/hospitalService'
import { getErrorMessage } from '../utils/errors'

const LABELS = { hospital: 'Hospital', clinic: 'Clinic', pharmacy: 'Pharmacy', emergency: 'Emergency facility' }
const mapLink = (f) => `https://www.openstreetmap.org/?mlat=${f.latitude}&mlon=${f.longitude}#map=17/${f.latitude}/${f.longitude}`

export function FacilityList({ result }) {
  if (!result) return null
  return (
    <div className="mt-6">
      {result.facilities.length === 0 ? (
        <EmptyState title="No facilities found">Try a larger search distance or a different type.</EmptyState>
      ) : (
        <ul className="space-y-3">
          {result.facilities.map((facility, index) => (
            <li key={`${facility.latitude}-${facility.longitude}-${index}`}>
              <Card>
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <h2 className="text-lg font-bold">{facility.name}</h2>
                  <span className="rounded-full bg-brand-50 px-3 py-1 text-sm font-semibold text-brand-800">{LABELS[facility.facility_type] || facility.facility_type}</span>
                </div>
                {facility.address && <p className="text-slate-700">{facility.address}</p>}
                {facility.distance_km != null && <p className="text-sm font-semibold text-slate-600">{facility.distance_km} km away</p>}
                <div className="mt-3 flex flex-wrap gap-2">
                  {facility.phone && <a href={`tel:${facility.phone.replace(/[^0-9+]/g, '')}`} className="inline-flex min-h-11 items-center gap-1 rounded-xl bg-brand-700 px-4 font-semibold text-white"><Phone className="size-4" aria-hidden /> Call {facility.phone}</a>}
                  <a href={mapLink(facility)} target="_blank" rel="noreferrer" className="inline-flex min-h-11 items-center gap-1 rounded-xl border-2 border-brand-700 px-4 font-semibold text-brand-800"><ExternalLink className="size-4" aria-hidden /> View on map</a>
                </div>
              </Card>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-4 text-sm text-slate-600">
        Data: <a className="underline" href={result.attribution_url} target="_blank" rel="noreferrer">{result.attribution}</a>. Listings are community-maintained and may be incomplete or out of date: call before travelling.
      </p>
    </div>
  )
}

// Shared by the patient/doctor hospital page and the admin lookup tool.
export default function FacilitySearch({ defaultCategory = '' }) {
  const { locate, locating, error: locationError } = useGeolocation()
  const [mode, setMode] = useState('location')
  const [city, setCity] = useState('')
  const [pincode, setPincode] = useState('')
  const [category, setCategory] = useState(defaultCategory)
  const [radius, setRadius] = useState(5000)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const search = async (event) => {
    event?.preventDefault()
    setError(''); setLoading(true)
    try {
      const params = { radius, ...(category ? { category } : {}) }
      if (mode === 'location') Object.assign(params, await locate())
      else {
        if (!city.trim() && !pincode.trim()) throw new Error('Enter a city or PIN code.')
        if (city.trim()) params.city = city.trim()
        if (pincode.trim()) params.pincode = pincode.trim()
      }
      setResult(await hospitalService.nearby(params))
    } catch (err) { setError(err.response ? getErrorMessage(err) : err.message) } finally { setLoading(false) }
  }

  return (
    <div>
      <Card>
        <form onSubmit={search} className="space-y-4">
          <div className="flex gap-2" role="group" aria-label="Search method">
            {[['location', 'Use my location'], ['place', 'City or PIN code']].map(([value, label]) => (
              <button type="button" key={value} aria-pressed={mode === value} onClick={() => setMode(value)}
                className={`min-h-12 flex-1 rounded-xl border-2 font-semibold ${mode === value ? 'border-brand-700 bg-brand-700 text-white' : 'border-slate-300 bg-white'}`}>{label}</button>
            ))}
          </div>
          {mode === 'place' && (
            <div className="grid gap-4 sm:grid-cols-2">
              <Field id="f-city" label="City / town"><input id="f-city" className={inputClass} value={city} onChange={(e) => setCity(e.target.value)} /></Field>
              <Field id="f-pin" label="PIN code"><input id="f-pin" inputMode="numeric" className={inputClass} value={pincode} onChange={(e) => setPincode(e.target.value)} /></Field>
            </div>
          )}
          <div className="grid gap-4 sm:grid-cols-2">
            <Field id="f-cat" label="Type">
              <select id="f-cat" className={inputClass} value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="">All</option>
                {FACILITY_CATEGORIES.map((c) => <option key={c} value={c}>{LABELS[c]}</option>)}
              </select>
            </Field>
            <Field id="f-radius" label="Distance">
              <select id="f-radius" className={inputClass} value={radius} onChange={(e) => setRadius(Number(e.target.value))}>
                {[2000, 5000, 10000, 25000].map((r) => <option key={r} value={r}>{r / 1000} km</option>)}
              </select>
            </Field>
          </div>
          {(error || locationError) && <Alert tone="error">{error || locationError}</Alert>}
          <Button type="submit" loading={loading || locating} className="w-full">
            {mode === 'location' ? <LocateFixed className="size-5" aria-hidden /> : <Search className="size-5" aria-hidden />} Search
          </Button>
          <p className="text-sm text-slate-600">Your location or city is sent to OpenStreetMap services to find places. It is not saved.</p>
        </form>
      </Card>
      <FacilityList result={result} />
    </div>
  )
}
