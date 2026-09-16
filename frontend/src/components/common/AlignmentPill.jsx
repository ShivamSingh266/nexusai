import { cn } from '../../lib/utils'

export function AlignmentPill({ status = 'aligned', score, tooltip }) {
  const styles = {
    aligned: 'bg-emerald-100 text-emerald-700',
    partial: 'bg-amber-100 text-amber-700',
    gap: 'bg-rose-100 text-rose-700',
  }

  return (
    <div className="inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-xs font-semibold" title={tooltip}>
      <span className={cn('rounded-full px-2 py-1 capitalize', styles[status] || styles.partial)}>
        {status}
      </span>
      {score !== undefined && <span className="text-slate-500">{score}%</span>}
    </div>
  )
}
