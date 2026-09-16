import { cn } from '../../lib/utils'

export function PriorityTag({ priority = 'medium' }) {
  const tones = {
    high: 'bg-rose-100 text-rose-700',
    medium: 'bg-amber-100 text-amber-700',
    low: 'bg-emerald-100 text-emerald-700',
  }

  return (
    <span className={cn('inline-flex rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.12em]', tones[priority] || tones.medium)}>
      {priority}
    </span>
  )
}
