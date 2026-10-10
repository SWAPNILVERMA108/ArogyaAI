import {
  Activity, BookHeart, Building2, FileText, Home, LogOut, MessageCircle, Pill, Siren, User, Users,
} from 'lucide-react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import Disclaimer from '../components/Disclaimer'
import LanguageSwitcher from '../components/LanguageSwitcher'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../context/LanguageContext'

const NAV_BY_ROLE = {
  PATIENT: [
    ['/dashboard', 'nav.dashboard', Home], ['/chat', 'nav.chat', MessageCircle], ['/reports', 'nav.reports', FileText],
    ['/medicines', 'nav.medicines', Pill], ['/hospitals', 'nav.hospitals', Building2],
    ['/health-tips', 'nav.tips', BookHeart], ['/emergency', 'nav.emergency', Siren], ['/profile', 'nav.profile', User],
  ],
  DOCTOR: [
    ['/doctor/dashboard', 'nav.dashboard', Home], ['/doctor/patients', 'nav.patients', Users],
    ['/hospitals', 'nav.hospitals', Building2], ['/profile', 'nav.profile', User],
  ],
  ADMIN: [
    ['/admin/dashboard', 'nav.dashboard', Home], ['/admin/users', 'nav.users', Users],
    ['/admin/hospitals', 'nav.hospitals', Building2], ['/profile', 'nav.profile', User],
  ],
}

export default function AppLayout() {
  const { user, logout } = useAuth()
  const { t } = useLanguage()
  const navigate = useNavigate()
  const items = NAV_BY_ROLE[user.role] || []

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  const linkClass = ({ isActive }) =>
    `flex items-center gap-2 rounded-xl px-3 py-2 text-base font-semibold ${isActive ? 'bg-brand-700 text-white' : 'text-slate-700 hover:bg-brand-50'}`

  return (
    <div className="min-h-screen pb-24 lg:pb-0">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
          <NavLink to="/" className="flex items-center gap-2 text-xl font-bold text-brand-800">
            <Activity className="size-7" aria-hidden /> {t('appName')}
          </NavLink>
          <nav aria-label="Main" className="hidden items-center gap-1 lg:flex">
            {items.map(([to, label, Icon]) => (
              <NavLink key={to} to={to} className={linkClass}><Icon className="size-5" aria-hidden />{t(label)}</NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <button onClick={handleLogout} className="flex min-h-10 items-center gap-1 rounded-lg px-2 text-slate-700 hover:bg-slate-100" aria-label={t('nav.logout')}>
              <LogOut className="size-5" aria-hidden /><span className="hidden sm:inline">{t('nav.logout')}</span>
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
        <Disclaimer className="mt-8" />
      </main>

      {/* Bottom navigation for phones: the first five items only, to keep it uncluttered. */}
      <nav aria-label="Mobile" className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-5 border-t border-slate-200 bg-white lg:hidden">
        {items.slice(0, 5).map(([to, label, Icon]) => (
          <NavLink key={to} to={to} className={({ isActive }) => `flex min-h-16 flex-col items-center justify-center gap-0.5 text-xs font-semibold ${isActive ? 'text-brand-700' : 'text-slate-600'}`}>
            <Icon className="size-6" aria-hidden />{t(label)}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
