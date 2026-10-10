import { Loader2, AlertTriangle, CheckCircle2, Info } from 'lucide-react'

const cx = (...parts) => parts.filter(Boolean).join(' ')

const variants = {
  primary: 'bg-brand-700 text-white hover:bg-brand-800 disabled:bg-slate-300',
  secondary: 'bg-white text-brand-800 border-2 border-brand-700 hover:bg-brand-50 disabled:opacity-50',
  danger: 'bg-red-600 text-white hover:bg-red-700 disabled:bg-slate-300',
  ghost: 'bg-transparent text-slate-700 hover:bg-slate-100 disabled:opacity-50',
}

export function Button({ variant = 'primary', loading = false, className, children, disabled, type = 'button', ...props }) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={cx(
        'inline-flex min-h-12 items-center justify-center gap-2 rounded-xl px-5 py-2 text-base font-semibold transition-colors disabled:cursor-not-allowed',
        variants[variant], className,
      )}
      {...props}
    >
      {loading && <Loader2 className="size-5 animate-spin" aria-hidden />}
      {children}
    </button>
  )
}

export function Card({ className, children, ...props }) {
  return <section className={cx('rounded-2xl border border-slate-200 bg-white p-5 shadow-sm', className)} {...props}>{children}</section>
}

export function Field({ label, error, hint, id, children }) {
  return (
    <div className="space-y-1">
      <label htmlFor={id} className="block text-base font-semibold text-slate-800">{label}</label>
      {children}
      {hint && !error && <p className="text-sm text-slate-600">{hint}</p>}
      {error && <p role="alert" className="text-sm font-medium text-red-700">{error}</p>}
    </div>
  )
}

export const inputClass =
  'block min-h-12 w-full rounded-xl border-2 border-slate-300 bg-white px-4 py-2 text-base placeholder:text-slate-400 focus:border-brand-600'

const alertStyles = {
  error: ['border-red-300 bg-red-50 text-red-900', AlertTriangle],
  success: ['border-emerald-300 bg-emerald-50 text-emerald-900', CheckCircle2],
  info: ['border-sky-300 bg-sky-50 text-sky-900', Info],
  warning: ['border-amber-300 bg-amber-50 text-amber-900', AlertTriangle],
}

export function Alert({ tone = 'info', children, className }) {
  const [style, Icon] = alertStyles[tone]
  return (
    <div role={tone === 'error' ? 'alert' : 'status'} className={cx('flex gap-3 rounded-xl border p-4 text-base', style, className)}>
      <Icon className="mt-0.5 size-5 shrink-0" aria-hidden />
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  )
}

export function Spinner({ label = 'Loading…' }) {
  return (
    <div role="status" className="flex items-center justify-center gap-3 py-10 text-slate-600">
      <Loader2 className="size-6 animate-spin" aria-hidden /> <span>{label}</span>
    </div>
  )
}

export function EmptyState({ icon: Icon, title, children }) {
  return (
    <div className="rounded-2xl border-2 border-dashed border-slate-300 p-8 text-center text-slate-600">
      {Icon && <Icon className="mx-auto mb-3 size-10 text-slate-400" aria-hidden />}
      <p className="text-lg font-semibold text-slate-800">{title}</p>
      {children && <div className="mt-1">{children}</div>}
    </div>
  )
}

export function PageHeader({ title, subtitle, action }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{title}</h1>
        {subtitle && <p className="mt-1 text-slate-600">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

// Shows load/error states, then renders children once data is ready.
export function AsyncBoundary({ loading, error, onRetry, children }) {
  if (loading) return <Spinner />
  if (error) {
    return (
      <Alert tone="error">
        <p>{error}</p>
        {onRetry && <Button variant="secondary" className="mt-3" onClick={onRetry}>Try again</Button>}
      </Alert>
    )
  }
  return children
}
