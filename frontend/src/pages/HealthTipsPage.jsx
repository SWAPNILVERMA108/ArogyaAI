import { useState } from 'react'
import Disclaimer from '../components/Disclaimer'
import { AsyncBoundary, Card, EmptyState, PageHeader } from '../components/ui'
import { useLanguage } from '../context/LanguageContext'
import { useAsync } from '../hooks/useAsync'
import { healthService } from '../services/healthService'

export default function HealthTipsPage() {
  const { t, pick, language } = useLanguage()
  const [category, setCategory] = useState('')
  const categories = useAsync(() => healthService.categories(), [])
  const tips = useAsync(() => healthService.tips(category), [category])

  return (
    <div>
      <PageHeader title={t('nav.tips')} subtitle={t('dashboard.cards.tips.1')} />
      <AsyncBoundary loading={categories.loading} error={categories.error} onRetry={categories.reload}>
        <div className="mb-5 flex flex-wrap gap-2" role="group" aria-label="Categories">
          {[{ slug: '', name: 'All', name_hi: 'सभी' }, ...(categories.data || [])].map((item) => (
            <button
              key={item.slug || 'all'}
              aria-pressed={category === item.slug}
              onClick={() => setCategory(item.slug)}
              className={`min-h-11 rounded-full border-2 px-4 font-semibold ${category === item.slug ? 'border-brand-700 bg-brand-700 text-white' : 'border-slate-300 bg-white'}`}
            >
              {pick(item, 'name')}
            </button>
          ))}
        </div>
      </AsyncBoundary>
      <AsyncBoundary loading={tips.loading} error={tips.error} onRetry={tips.reload}>
        {tips.data?.tips.length === 0 ? <EmptyState title="No tips yet" /> : (
          <div className="grid gap-4 sm:grid-cols-2">
            {tips.data?.tips.map((tip) => (
              <Card key={tip.id}>
                <h2 className="text-xl font-bold">{pick(tip, 'title')}</h2>
                <p className="mt-2 text-slate-700">{pick(tip, 'body')}</p>
              </Card>
            ))}
          </div>
        )}
        {tips.data && <Disclaimer className="mt-6" text={language === 'hi' ? tips.data.disclaimer_hi : tips.data.disclaimer} />}
      </AsyncBoundary>
    </div>
  )
}
