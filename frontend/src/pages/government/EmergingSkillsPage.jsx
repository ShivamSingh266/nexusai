import { AppShell } from '../../components/layout/AppShell'
import { PageContainer } from '../../components/layout/PageContainer'
import { Card } from '../../components/ui/Card'
import { emergingSkillsData } from '../../mocks/governmentMockData'

export function EmergingSkillsPage() {
  return (
    <AppShell title="Government Dashboard">
      <PageContainer>
        <div className="border-b border-slate-200 pb-6">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Government</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Emerging Skills</h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-600">
            Identify skills that are beginning to create a new labor demand and may warrant policy or training intervention.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {emergingSkillsData.map((skill) => (
            <Card key={skill.name} className="p-5">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-lg font-semibold text-slate-900">{skill.name}</h2>
                <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-700">
                  {skill.priority}
                </span>
              </div>

              <div className="mt-4 space-y-3 text-sm text-slate-600">
                <div className="flex items-center justify-between">
                  <span>Growth</span>
                  <span className="font-semibold text-slate-900">+{skill.growth}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Sector</span>
                  <span className="font-medium text-slate-700">{skill.sector}</span>
                </div>
              </div>

              <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Government action</div>
                <div className="mt-2 text-sm text-slate-700">{skill.action}</div>
              </div>
            </Card>
          ))}
        </div>
      </PageContainer>
    </AppShell>
  )
}
