import { cn } from '../../lib/utils'

export function LoadingSkeleton({ variant = 'card', className = '' }) {
  const variants = {
    card: 'h-28 rounded-2xl',
    table: 'h-12 rounded-xl',
    list: 'h-16 rounded-xl',
    timeline: 'h-20 rounded-2xl',
    avatar: 'h-12 w-12 rounded-full',
  }

  return (
    <div
      className={cn(
        'animate-pulse bg-gradient-to-r from-slate-200 via-slate-100 to-slate-200',
        variants[variant],
        className,
      )}
    />
  )
}
