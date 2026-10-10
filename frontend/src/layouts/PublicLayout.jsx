import { Activity } from 'lucide-react'
import { Link, Outlet } from 'react-router-dom'
import Disclaimer from '../components/Disclaimer'
import LanguageSwitcher from '../components/LanguageSwitcher'
import { useLanguage } from '../context/LanguageContext'

export default function PublicLayout() {
  const { t } = useLanguage()
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
        <Link to="/" className="flex items-center gap-2 text-xl font-bold text-brand-800">
          <Activity className="size-7" aria-hidden /> {t('appName')}
        </Link>
        <LanguageSwitcher />
      </header>
      <main className="mx-auto max-w-5xl px-4 pb-10"><Outlet /><Disclaimer className="mt-8" /></main>
    </div>
  )
}
