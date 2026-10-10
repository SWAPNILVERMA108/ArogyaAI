import { ShieldAlert } from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'

export default function Disclaimer({ text, className = '' }) {
  const { t } = useLanguage()
  return (
    <p className={`flex gap-2 rounded-xl bg-amber-50 p-3 text-sm text-amber-900 ${className}`}>
      <ShieldAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
      <span>{text || t('common.disclaimer')}</span>
    </p>
  )
}
