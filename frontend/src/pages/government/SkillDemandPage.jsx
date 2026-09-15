import { AppShell } from '../../components/layout/AppShell'
import { PageContainer } from '../../components/layout/PageContainer'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { GovernmentStatCard } from '../../components/government/GovernmentStatCard'
import { skillDemandData } from '../../mocks/governmentMockData'

export function SkillDemandPage() {
  return (
    <AppShell title="Government Dashboard">
      <PageContainer>
        <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Government</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Skill Demand</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              Monitor the skills most in demand across public and private sectors to guide workforce planning.
            </p>
          </div>
          <Button variant="secondary">Export view</Button>
        </div>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <GovernmentStatCard label="Most Demanded" value="AI & ML" detail="92% demand score" />
          <GovernmentStatCard label="Trending Skills" value="6" detail="Across 4 sectors" />
          <GovernmentStatCard label="Top Growth" value="+28%" detail="AI & ML growth" />
          <GovernmentStatCard label="Regional Readiness" value="81%" detail="Average readiness" />
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.5fr_0.8fr]">
          <Card className="p-5">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Most demanded skills</h2>
            </div>
            <div className="space-y-4">
              {skillDemandData.map((skill) => (
                <div key={skill.name}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="font-medium text-slate-700">{skill.name}</span>
                    <span className="text-slate-500">{skill.demand}%</span>
                  </div>
                  <div className="h-2.5 rounded-full bg-slate-200">
                    <div className="h-2.5 rounded-full bg-brand-600" style={{ width: `${skill.demand}%` }} />
                  </div>
                  <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
                    <span>{skill.sector}</span>
                    <span>Growth +{skill.growth}%</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="text-lg font-semibold text-slate-900">Trending / upcoming</h2>
            <div className="mt-4 space-y-3">
              {['AI Governance', 'Responsible AI', 'Prompt Engineering', 'Cloud Security'].map((skill) => (
                <div key={skill} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="font-medium text-slate-800">{skill}</div>
                  <div className="mt-1 text-xs text-slate-500">Pipeline trend: expected to rise over the next 6-12 months</div>
                </div>
              ))}
            </div>
          </Card>
        </section>

        <Card className="p-5">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-slate-900">Sector demand overview</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {skillDemandData.slice(0, 3).map((skill) => (
              <div key={skill.name} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div className="text-sm font-semibold text-slate-900">{skill.name}</div>
                <div className="mt-2 text-xs text-slate-500">Sector: {skill.sector}</div>
                <div className="mt-3 flex items-center justify-between text-sm text-slate-700">
                  <span>Demand</span>
                  <span className="font-semibold">{skill.demand}%</span>
                </div>
                <div className="mt-2 h-2 rounded-full bg-slate-200">
                  <div className="h-2 rounded-full bg-emerald-500" style={{ width: `${skill.demand}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </PageContainer>
    </AppShell>
  )
}
