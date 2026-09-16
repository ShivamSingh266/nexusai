import { cn } from '../../lib/utils'

export function MatchScoreBadge({ score = 0 }) {
  const tone = score >= 80
    ? 'bg-emerald-100 text-emerald-700'
    : score >= 60
      ? 'bg-amber-100 text-amber-700'
      : score >= 40
        ? 'bg-orange-100 text-orange-700'
        : 'bg-rose-100 text-rose-700'

  return (
    <span className={cn('inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold', tone)}>
      {score}% match
    </span>
  )
}
