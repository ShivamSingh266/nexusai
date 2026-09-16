import { cn } from '../../lib/utils'

export function Card({ children, className = '' }) {
  return (
    <div
      className={cn(
        'rounded-2xl border border-slate-200 bg-white/80 shadow-soft backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/90',
        className,
      )}
    >
      {children}
    </div>
  )
}
