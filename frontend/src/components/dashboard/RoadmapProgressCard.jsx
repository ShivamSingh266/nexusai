export function RoadmapProgressCard({ completed = 0, remaining = 0, total = 0 }) {
  const percent = total ? Math.round((completed / total) * 100) : 0

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-900">Roadmap Progress</h3>
        <span className="text-sm font-medium text-brand-700">{percent}%</span>
      </div>

      <div className="mt-4 h-2.5 rounded-full bg-slate-200">
        <div className="h-2.5 rounded-full bg-brand-600" style={{ width: `${percent}%` }} />
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
        <span>{completed} completed</span>
        <span>{remaining} remaining</span>
      </div>

      <p className="mt-4 text-xs text-slate-500">Total {total} milestones</p>
    </div>
  )
}
