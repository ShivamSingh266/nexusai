import { AppShell } from '../../components/layout/AppShell'
import { PageContainer } from '../../components/layout/PageContainer'
import { GovernmentStatCard } from '../../components/government/GovernmentStatCard'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import {
  governmentInsights,
  governmentKpis,
  regionalDemand,
  skillDemandData,
  trendData,
} from '../../mocks/governmentMockData'

export function GovernmentDashboardPage() {
  return (
    <AppShell title="Government Dashboard">
      <PageContainer>
        <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Government</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Government Command Center</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              Track workforce demand, align policy and learning programs, and prioritize actions that strengthen public-sector readiness.
            </p>
          </div>
          <Button variant="secondary">View reports</Button>
        </div>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {governmentKpis.map((item) => (
            <GovernmentStatCard key={item.label} label={item.label} value={item.value} detail={item.detail} />
          ))}
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
          <Card className="p-5">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Skill demand overview</h2>
            </div>

            <div className="space-y-4">
              {skillDemandData.slice(0, 4).map((skill) => (
                <div key={skill.name}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="font-medium text-slate-700">{skill.name}</span>
                    <span className="text-slate-500">{skill.demand}%</span>
                  </div>
                  <div className="h-2.5 rounded-full bg-slate-200">
                    <div className="h-2.5 rounded-full bg-brand-600" style={{ width: `${skill.demand}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="text-lg font-semibold text-slate-900">Regional demand</h2>
            <div className="mt-4 space-y-4">
              {regionalDemand.map((region) => (
                <div key={region.region}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="font-medium text-slate-700">{region.region}</span>
                    <span className="text-slate-500">{region.demand}</span>
                  </div>
                  <div className="h-2.5 rounded-full bg-slate-200">
                    <div className="h-2.5 rounded-full bg-emerald-500" style={{ width: `${region.share}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <Card className="p-5">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-slate-900">Employment & talent trends</h2>
            </div>
            <div className="flex h-52 items-end gap-3">
              {trendData.map((point) => (
                <div key={point.month} className="flex flex-1 flex-col items-center gap-2">
                  <div className="w-full rounded-t-xl bg-brand-100" style={{ height: `${point.value}%` }} />
                  <span className="text-xs text-slate-500">{point.month}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="text-lg font-semibold text-slate-900">Recent insights</h2>
            <div className="mt-4 space-y-3">
              {governmentInsights.map((insight) => (
                <div key={insight.title} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="font-medium text-slate-800">{insight.title}</div>
                  <p className="mt-2 text-sm text-slate-600">{insight.detail}</p>
                </div>
              ))}
            </div>
          </Card>
        </section>
      </PageContainer>
    </AppShell>
  )
}
