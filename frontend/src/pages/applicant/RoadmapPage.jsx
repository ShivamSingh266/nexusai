import { applicantRoadmap } from '../../data/applicantMockData'

export function RoadmapPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Roadmap</p>
        <h2 className="mt-2 text-3xl font-bold text-slate-900">Career roadmap</h2>
      </div>

      <div className="space-y-3 rounded-3xl border border-slate-200 bg-white p-5">
        {applicantRoadmap.map((item, index) => (
          <div key={item.label} className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-3">
            <div className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold ${item.done ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-600'}`}>
              {item.done ? '✓' : index + 1}
            </div>
            <span className="text-sm font-medium text-slate-700">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
