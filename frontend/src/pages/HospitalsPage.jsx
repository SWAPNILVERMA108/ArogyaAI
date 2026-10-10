import FacilitySearch from '../components/FacilitySearch'
import { PageHeader } from '../components/ui'
import { useLanguage } from '../context/LanguageContext'

export default function HospitalsPage() {
  const { t } = useLanguage()
  return (
    <div>
      <PageHeader title={t('dashboard.cards.hospitals.0')} subtitle={t('dashboard.cards.hospitals.1')} />
      <FacilitySearch />
    </div>
  )
}
