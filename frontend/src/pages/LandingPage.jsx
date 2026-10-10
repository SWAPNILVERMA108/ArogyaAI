import { HeartPulse, Mic, FileText, MapPin } from 'lucide-react'
import { Link, Navigate } from 'react-router-dom'
import { Button } from '../components/ui'
import { HOME_BY_ROLE } from '../constants'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../context/LanguageContext'

export default function LandingPage() {
  const { user } = useAuth()
  const { t } = useLanguage()
  if (user) return <Navigate to={HOME_BY_ROLE[user.role]} replace />

  const features = [
    [HeartPulse, 'dashboard.cards.chat'], [Mic, 'dashboard.cards.voice'],
    [FileText, 'dashboard.cards.reports'], [MapPin, 'dashboard.cards.hospitals'],
  ]
  return (
    <div className="py-8 text-center sm:py-14">
      <h1 className="text-4xl font-extrabold text-brand-800 sm:text-5xl">{t('appName')}</h1>
      <p className="mx-auto mt-4 max-w-xl text-xl text-slate-700">{t('tagline')}</p>
      <div className="mt-8 flex flex-wrap justify-center gap-4">
        <Link to="/register"><Button className="px-8 text-lg">{t('nav.register')}</Button></Link>
        <Link to="/login"><Button variant="secondary" className="px-8 text-lg">{t('nav.login')}</Button></Link>
      </div>
      <ul className="mx-auto mt-12 grid max-w-3xl gap-4 text-left sm:grid-cols-2">
        {features.map(([Icon, key]) => (
          <li key={key} className="flex items-start gap-3 rounded-2xl bg-white p-4 shadow-sm">
            <Icon className="mt-1 size-7 shrink-0 text-brand-700" aria-hidden />
            <div><p className="font-bold">{t(`${key}.0`)}</p><p className="text-slate-600">{t(`${key}.1`)}</p></div>
          </li>
        ))}
      </ul>
    </div>
  )
}
