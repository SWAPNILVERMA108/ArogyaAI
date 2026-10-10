import FacilitySearch from '../../components/FacilitySearch'
import { Alert, PageHeader } from '../../components/ui'

export default function AdminHospitalsPage() {
  return (
    <div>
      <PageHeader title="Facility lookup" subtitle="Check what healthcare facilities patients will see in an area." />
      <Alert tone="info" className="mb-4">Facilities are fetched live from OpenStreetMap, not stored in ArogyaAI, so there is nothing to edit here. To correct a listing, fix it on OpenStreetMap.</Alert>
      <FacilitySearch />
    </div>
  )
}
