import { MatchScoreBadge } from '../common/MatchScoreBadge'

export function JobPreviewCard({ title, company, location, salary, matchScore = 0 }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-slate-900">{title}</h3>
          <p className="mt-1 text-sm text-slate-500">{company}</p>
        </div>
        <MatchScoreBadge score={matchScore} />
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-slate-500">
        <span>{location}</span>
        <span>•</span>
        <span>{salary}</span>
      </div>
    </div>
  )
}
