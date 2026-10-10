import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { LANGUAGES, translations } from '../constants/translations'

const LanguageContext = createContext(null)
const STORAGE_KEY = 'arogyaai.language'

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    return LANGUAGES.some((item) => item.code === saved) ? saved : 'en'
  })

  useEffect(() => { document.documentElement.lang = language }, [language])

  const setLanguage = useCallback((code) => {
    localStorage.setItem(STORAGE_KEY, code)
    setLanguageState(code)
  }, [])

  // t('nav.chat') -> translated text; falls back to English, then to the key.
  const t = useCallback((path) => {
    const lookup = (lang) => path.split('.').reduce((node, key) => node?.[key], translations[lang])
    return lookup(language) ?? lookup('en') ?? path
  }, [language])

  // Pick the localised variant of a bilingual API field, e.g. pick(tip, 'title').
  const pick = useCallback((item, field) => (language === 'hi' && item[`${field}_hi`]) || item[field], [language])

  const value = useMemo(() => ({ language, setLanguage, t, pick }), [language, setLanguage, t, pick])
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

export const useLanguage = () => {
  const context = useContext(LanguageContext)
  if (!context) throw new Error('useLanguage must be used inside LanguageProvider')
  return context
}
