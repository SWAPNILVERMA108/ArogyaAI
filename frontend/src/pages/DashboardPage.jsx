import { BookHeart, Building2, FileText, MessageCircle, Mic, Pill, Siren, Clock } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Card } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../context/LanguageContext'
import { useAsync } from '../hooks/useAsync'
import { medicineService } from '../services/medicineService'
import { todaysReminders } from '../utils/reminders'
import { formatTime } from '../utils/format'

const CARDS = [
  ['chat', '/chat', MessageCircle, 'bg-emerald-100 text-emerald-800'],
  ['voice', '/chat?voice=1', Mic, 'bg-sky-100 text-sky-800'],
  ['reports', '/reports', FileText, 'bg-violet-100 text-violet-800'],
  ['medicines', '/medicines', Pill, 'bg-amber-100 text-amber-800'],
  ['hospitals', '/hospitals', Building2, 'bg-teal-100 text-teal-800'],
  ['emergency', '/emergency', Siren, 'bg-red-100 text-red-800'],
  ['tips', '/health-tips', BookHeart, 'bg-lime-100 text-lime-800'],
]
export default function DashboardPage() {
  const { user } = useAuth()
  const { t } = useLanguage()
  const { data: medicines } = useAsync(() => medicineService.list(), [])
  const reminders = medicines ? todaysReminders(medicines) : []

  return (
    <div>
      <h1 className="text-3xl font-bold">{t('dashboard.greeting')}, {user.name.split(' ')[0]}</h1>
      <p className="mb-6 mt-1 text-lg text-slate-600">{t('dashboard.subtitle')}</p>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {CARDS.map(([key, to, Icon, color]) => (
          <Link key={key} to={to} className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-brand-600 hover:shadow-md">
            <span className={`mb-3 inline-flex size-14 items-center justify-center rounded-2xl ${color}`}><Icon className="size-8" aria-hidden /></span>
            <h2 className="text-xl font-bold group-hover:text-brand-800">{t(`dashboard.cards.${key}.0`)}</h2>
            <p className="text-slate-600">{t(`dashboard.cards.${key}.1`)}</p>
          </Link>
        ))}
      </div>

      {reminders.length > 0 && (
        <Card className="mt-6">
          <h2 className="mb-3 flex items-center gap-2 text-xl font-bold"><Clock className="size-5" aria-hidden /> Today&apos;s medicine times</h2>
          <ul className="divide-y divide-slate-100">
            {reminders.map((item) => (
              <li key={item.id} className="flex items-center justify-between py-2">
                <span className="font-semibold">{item.name}{item.dosage && <span className="font-normal text-slate-600"> · {item.dosage}</span>}</span>
                <span className="text-lg font-bold text-brand-800">{formatTime(item.time)}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  )
}
