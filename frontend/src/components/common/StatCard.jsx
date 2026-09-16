import { cn } from '../../lib/utils'

export function StatCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  variant = 'default',
  loading = false,
  className = '',
}) {
  const variants = {
    default: 'border-slate-200 bg-white',
    success: 'border-emerald-200 bg-emerald-50/60',
    warning: 'border-amber-200 bg-amber-50/60',
    brand: 'border-brand-200 bg-brand-50/60',
  }

  if (loading) {
    return (
      <div className={cn('rounded-2xl border border-slate-200 bg-slate-100 p-5', className)}>
        <div className="h-4 w-24 animate-pulse rounded bg-slate-200" />
        <div className="mt-4 h-8 w-20 animate-pulse rounded bg-slate-200" />
        <div className="mt-3 h-4 w-32 animate-pulse rounded bg-slate-200" />
      </div>
    )
  }

  return (
    <div className={cn('rounded-2xl border p-5 shadow-sm', variants[variant], className)}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm text-slate-500">{title}</p>
          <p className="mt-3 text-3xl font-bold tracking-tight text-slate-900">{value}</p>
        </div>

        {icon && (
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-lg shadow-sm">
            {icon}
          </div>
        )}
      </div>

      <div className="mt-3 flex items-center gap-2 text-xs font-medium">
        {trend && (
          <span className={cn('rounded-full px-2 py-1', trend.startsWith('+') ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700')}>
            {trend}
          </span>
        )}
        {subtitle && <span className="text-slate-500">{subtitle}</span>}
      </div>
    </div>
  )
}
