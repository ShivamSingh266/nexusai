import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, TrendingUp, Layers, Award, ArrowUpRight } from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StatCard } from '../../components/common/StatCard'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { LineTrendChart } from '../../components/charts/LineTrendChart'
import { governmentService } from '../../services/governmentService'
import { trendData, governmentInsights } from '../../mocks/governmentMockData'

export function GovernmentDashboardPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [kpis, setKpis] = useState([])
  const [skillDemand, setSkillDemand] = useState([])
  const [regionalDemand, setRegionalDemand] = useState([])

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [kpiRes, skillRes, regionRes] = await Promise.all([
          governmentService.getKpis(),
          governmentService.getSkillDemand(),
          governmentService.getRegionalDemand(),
        ])
        setKpis(kpiRes)
        setSkillDemand(skillRes)
        setRegionalDemand(regionRes)
      } finally {
        setLoading(false)
      }
    }

    loadDashboardData()
  }, [])

  const kpiIcons = [
    <Layers key="1" className="h-5 w-5 text-brand-600" />,
    <TrendingUp key="2" className="h-5 w-5 text-emerald-600" />,
    <FileText key="3" className="h-5 w-5 text-indigo-600" />,
    <Award key="4" className="h-5 w-5 text-amber-600" />,
  ]

  const qualitativeLevelStyles = {
    'Very High': { width: '95%', color: 'bg-indigo-600', badge: 'bg-indigo-100 text-indigo-800' },
    High: { width: '75%', color: 'bg-emerald-600', badge: 'bg-emerald-100 text-emerald-800' },
    Moderate: { width: '50%', color: 'bg-amber-500', badge: 'bg-amber-100 text-amber-800' },
    Low: { width: '25%', color: 'bg-slate-400', badge: 'bg-slate-100 text-slate-700' },
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Government</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Government Command Center</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
            Track workforce demand, align policy and learning programs, and prioritize actions that strengthen public-sector readiness.
          </p>
        </div>

        <Button
          variant="secondary"
          onClick={() => navigate('/government/reports')}
          className="inline-flex items-center gap-2"
        >
          <FileText className="h-4 w-4" />
          <span>View Reports</span>
        </Button>
      </div>

      {/* KPI Cards */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {loading ? (
          <>
            <LoadingSkeleton variant="card" />
            <LoadingSkeleton variant="card" />
            <LoadingSkeleton variant="card" />
            <LoadingSkeleton variant="card" />
          </>
        ) : (
          kpis.map((item, index) => (
            <StatCard
              key={item.label}
              title={item.label}
              value={item.value}
              subtitle={item.detail}
              icon={kpiIcons[index % kpiIcons.length]}
              trend={item.detail.startsWith('+') ? item.detail : undefined}
            />
          ))
        )}
      </section>

      {/* Skill Demand Overview & Regional Demand */}
      <section className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <Card className="p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Skill Demand Overview</h2>
              <p className="text-xs text-slate-500">Industry demand index across key national competency areas</p>
            </div>
            <button
              type="button"
              onClick={() => navigate('/government/skill-demand')}
              className="inline-flex items-center gap-1 text-xs font-medium text-brand-700 hover:text-brand-800"
            >
              Explore all <ArrowUpRight className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="space-y-4 pt-1">
            {skillDemand.slice(0, 4).map((skill) => (
              <div key={skill.name}>
                <div className="mb-1.5 flex items-center justify-between text-sm">
                  <span className="font-semibold text-slate-800">{skill.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-brand-700">{skill.demand}%</span>
                    <span className="text-[11px] text-slate-400">+{skill.growth}% growth</span>
                  </div>
                </div>
                <div className="h-3 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-brand-600 transition-all duration-500"
                    style={{ width: `${skill.demand}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Regional Demand */}
        <Card className="p-5">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-slate-900">Regional Demand</h2>
            <p className="text-xs text-slate-500">Qualitative workforce requirement intensity by jurisdiction</p>
          </div>

          <div className="space-y-4 pt-1">
            {regionalDemand.map((region) => {
              const style = qualitativeLevelStyles[region.demand] || qualitativeLevelStyles.Moderate
              return (
                <div key={region.region} className="rounded-xl border border-slate-100 bg-slate-50/50 p-3">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-semibold text-slate-800">{region.region} Region</span>
                    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${style.badge}`}>
                      {region.demand}
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-200 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${style.color} transition-all duration-500`}
                      style={{ width: style.width }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </Card>
      </section>

      {/* Employment & Talent Trends and Recent Insights */}
      <section className="grid gap-6 xl:grid-cols-[1.3fr_0.9fr]">
        <Card className="p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Employment & Talent Trends</h2>
              <p className="text-xs text-slate-500">Quarterly talent readiness velocity (%)</p>
            </div>
          </div>
          <LineTrendChart data={trendData} height={200} strokeColor="#2563eb" fillColor="#3b82f6" />
        </Card>

        <Card className="p-5">
          <h2 className="text-lg font-semibold text-slate-900">Recent Insights</h2>
          <p className="text-xs text-slate-500 mb-4">Labour market signals requiring policy attention</p>
          <div className="space-y-3">
            {governmentInsights.map((insight) => (
              <div key={insight.title} className="rounded-xl border border-slate-200 bg-slate-50 p-3.5">
                <div className="font-semibold text-sm text-slate-800">{insight.title}</div>
                <p className="mt-1.5 text-xs leading-relaxed text-slate-600">{insight.detail}</p>
              </div>
            ))}
          </div>
        </Card>
      </section>
    </div>
  )
}

export default GovernmentDashboardPage
