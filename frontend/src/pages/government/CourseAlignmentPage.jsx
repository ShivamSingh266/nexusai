import { AppShell } from '../../components/layout/AppShell'
import { PageContainer } from '../../components/layout/PageContainer'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { courseAlignmentData } from '../../mocks/governmentMockData'

export function CourseAlignmentPage() {
  return (
    <AppShell title="Government Dashboard">
      <PageContainer>
        <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Government</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Course Alignment</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              Review how closely training programs match the skills required by current hiring and workforce needs.
            </p>
          </div>
          <Button variant="secondary">Refresh alignment</Button>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Card className="p-5">
            <p className="text-sm text-slate-500">Programs reviewed</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">{courseAlignmentData.length}</p>
          </Card>
          <Card className="p-5">
            <p className="text-sm text-slate-500">Strong alignment</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">2</p>
          </Card>
          <Card className="p-5">
            <p className="text-sm text-slate-500">Needs catch-up</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">2</p>
          </Card>
        </div>

        <div className="space-y-4">
          {courseAlignmentData.map((program) => (
            <Card key={program.program} className="p-5">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-slate-900">{program.program}</h2>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {program.skills.map((skill) => (
                      <span key={skill} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="w-full max-w-xs">
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="text-slate-600">Alignment score</span>
                    <span className="font-semibold text-slate-900">{program.alignment}%</span>
                  </div>
                  <div className="h-2.5 rounded-full bg-slate-200">
                    <div className="h-2.5 rounded-full bg-brand-600" style={{ width: `${program.alignment}%` }} />
                  </div>
                </div>
              </div>

              <div className="mt-5 grid gap-4 md:grid-cols-[0.8fr_1.2fr]">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Status</div>
                  <div className="mt-2 inline-flex rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                    {program.status}
                  </div>
                </div>
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Recommended action</div>
                  <div className="mt-2 text-sm text-slate-700">{program.gap}</div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </PageContainer>
    </AppShell>
  )
}
