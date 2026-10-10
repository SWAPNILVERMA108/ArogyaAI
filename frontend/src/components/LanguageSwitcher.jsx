import { Languages } from 'lucide-react'
import { LANGUAGES } from '../constants/translations'
import { useLanguage } from '../context/LanguageContext'

export default function LanguageSwitcher() {
  const { language, setLanguage, t } = useLanguage()
  return (
    <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
      <Languages className="size-5" aria-hidden />
      <span className="sr-only">{t('common.language')}</span>
      <select
        value={language}
        onChange={(event) => setLanguage(event.target.value)}
        className="min-h-10 rounded-lg border-2 border-slate-300 bg-white px-2"
      >
        {LANGUAGES.map((item) => <option key={item.code} value={item.code}>{item.label}</option>)}
      </select>
    </label>
  )
}
