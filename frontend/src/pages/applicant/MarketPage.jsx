import { MarketSparkline } from '../../components/dashboard/MarketSparkline'
import { applicantInsights } from '../../data/applicantMockData'

export function MarketPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Market</p>
        <h2 className="mt-2 text-3xl font-bold text-slate-900">Labour market trends</h2>
      </div>

      <div className="rounded-3xl border border-slate-200 bg-white p-5">
        <h3 className="text-lg font-semibold text-slate-900">Skill-market confidence</h3>
        <div className="mt-4">
          <MarketSparkline data={applicantInsights.trend} color="#22c55e" />
        </div>
      </div>
    </div>
  )
}
