import { ApplicantLayout } from '../../app/layouts/ApplicantLayout'
import { applicantInsights } from '../../data/applicantMockData'

export function SkillGapPage() {
  return (
    <ApplicantLayout>
      <div className="space-y-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Skill gap</p>
          <h2 className="mt-2 text-3xl font-bold text-slate-900">Skill gap analysis</h2>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {applicantInsights.skillGap.map((skill) => (
            <div key={skill.name} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-900">{skill.name}</h3>
                <span className="rounded-full bg-brand-50 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-brand-700">
                  {skill.priority}
                </span>
              </div>

              <div className="mt-5 h-2.5 rounded-full bg-slate-200">
                <div className="h-2.5 rounded-full bg-brand-600" style={{ width: `${skill.gap}%` }} />
              </div>

              <p className="mt-3 text-sm text-slate-500">Gap score: {skill.gap}%</p>
            </div>
          ))}
        </div>
      </div>
    </ApplicantLayout>
  )
}
