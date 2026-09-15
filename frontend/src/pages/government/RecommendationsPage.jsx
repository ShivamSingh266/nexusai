import { AppShell } from '../../components/layout/AppShell'
import { PageContainer } from '../../components/layout/PageContainer'
import { Card } from '../../components/ui/Card'
import { recommendationsData } from '../../mocks/governmentMockData'

export function RecommendationsPage() {
  return (
    <AppShell title="Government Dashboard">
      <PageContainer>
        <div className="border-b border-slate-200 pb-6">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Government</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">AI Recommendations</h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-600">
            Review mock workforce and policy recommendations to guide public-sector action with confidence.
          </p>
        </div>

        <div className="space-y-4">
          {recommendationsData.map((item) => (
            <Card key={item.title} className="p-5">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-slate-900">{item.title}</h2>
                  <p className="mt-2 text-sm text-slate-600">{item.insight}</p>
                </div>
                <span className="rounded-full bg-brand-50 px-2.5 py-1 text-xs font-semibold text-brand-700">
                  {item.priority} priority
                </span>
              </div>

              <div className="mt-5 grid gap-4 md:grid-cols-3">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Suggested action</div>
                  <div className="mt-2 text-sm text-slate-700">{item.action}</div>
                </div>
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Expected impact</div>
                  <div className="mt-2 text-sm text-slate-700">{item.impact}</div>
                </div>
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Priority</div>
                  <div className="mt-2 text-sm text-slate-700">{item.priority}</div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </PageContainer>
    </AppShell>
  )
}
