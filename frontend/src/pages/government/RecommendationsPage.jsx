import { useEffect, useState } from 'react'
import { CheckCircle, AlertCircle, Lightbulb, Compass, Building, Users } from 'lucide-react'
import { Card } from '../../components/ui/Card'
import { PriorityTag } from '../../components/common/PriorityTag'
import { AccordionRow } from '../../components/common/AccordionRow'
import { StatCard } from '../../components/common/StatCard'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { governmentService } from '../../services/governmentService'

export function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const data = await governmentService.getRecommendations()
        setRecommendations(data)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-200 pb-6">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Government</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Workforce Policy Recommendations</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
          Transform live labour-market intelligence and skill shortages into targeted public-sector interventions, regional grants, and institutional partnerships.
        </p>
      </div>

      {/* Featured Strategic Callout: Increase AI Training Programs */}
      <div className="rounded-3xl border-2 border-brand-500/30 bg-gradient-to-br from-brand-50/80 via-white to-brand-50/40 p-6 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <PriorityTag priority="high" />
              <span className="text-xs font-semibold text-brand-700 uppercase tracking-wider">
                Immediate Action Required
              </span>
            </div>
            <h2 className="text-2xl font-bold text-slate-900">Increase AI Training Programs</h2>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
              National AI & ML demand is outpacing local talent output. Target the South region with university consortium partnerships to monitor talent readiness.
            </p>
          </div>

          <div className="shrink-0 rounded-2xl bg-white border border-brand-100 p-4 shadow-sm">
            <p className="text-xs font-medium text-slate-500">Projected Readiness Uplift</p>
            <p className="mt-1 text-2xl font-bold text-brand-700">+14% YoY</p>
          </div>
        </div>

        {/* 3 Action Pillars */}
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-white bg-white/90 p-4 shadow-sm">
            <div className="flex items-center gap-2 text-xs font-semibold text-brand-700">
              <Compass className="h-4 w-4" />
              <span>Target Region</span>
            </div>
            <p className="mt-1.5 text-base font-bold text-slate-800">Target South Region</p>
            <p className="mt-1 text-xs text-slate-500">High-concentration technology and advanced service corridor.</p>
          </div>

          <div className="rounded-2xl border border-white bg-white/90 p-4 shadow-sm">
            <div className="flex items-center gap-2 text-xs font-semibold text-brand-700">
              <Building className="h-4 w-4" />
              <span>Institutional Strategy</span>
            </div>
            <p className="mt-1.5 text-base font-bold text-slate-800">Partner with Universities</p>
            <p className="mt-1 text-xs text-slate-500">Co-develop applied AI lab curriculum and employer fellowships.</p>
          </div>

          <div className="rounded-2xl border border-white bg-white/90 p-4 shadow-sm">
            <div className="flex items-center gap-2 text-xs font-semibold text-brand-700">
              <Users className="h-4 w-4" />
              <span>Metric Target</span>
            </div>
            <p className="mt-1.5 text-base font-bold text-slate-800">Monitor Talent Readiness</p>
            <p className="mt-1 text-xs text-slate-500">Continuous skill assessment pipeline tracking graduate placement.</p>
          </div>
        </div>
      </div>

      {/* List of Detailed Recommendations via AccordionRow & StatCards */}
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-3">All Active Recommendations</h3>
        {loading ? (
          <div className="space-y-3">
            <LoadingSkeleton variant="card" />
            <LoadingSkeleton variant="card" />
          </div>
        ) : (
          <div className="space-y-4">
            {recommendations.map((rec) => (
              <AccordionRow
                key={rec.id || rec.title}
                title={
                  <div className="flex items-center gap-3">
                    <PriorityTag priority={rec.priority} />
                    <span className="text-base font-bold text-slate-900">{rec.title}</span>
                  </div>
                }
                summary={`${rec.target} • ${rec.region}`}
              >
                <div className="pt-2 space-y-4">
                  <p className="text-sm text-slate-700 leading-relaxed">{rec.detail}</p>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-xl border border-slate-100 bg-slate-50 p-3.5">
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                        Operational Action
                      </p>
                      <p className="mt-1 text-xs font-medium text-slate-800">{rec.action}</p>
                    </div>

                    <div className="rounded-xl border border-slate-100 bg-slate-50 p-3.5">
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                        Expected Labour Impact
                      </p>
                      <p className="mt-1 text-xs font-medium text-slate-800">{rec.impact}</p>
                    </div>
                  </div>

                  {rec.kpis && rec.kpis.length > 0 && (
                    <div className="grid gap-3 sm:grid-cols-3 pt-1">
                      {rec.kpis.map((kpi, idx) => (
                        <div key={idx} className="rounded-xl border border-slate-200 bg-white p-3 text-center">
                          <p className="text-xs text-slate-500">{kpi.label}</p>
                          <p className="mt-1 text-base font-bold text-brand-700">{kpi.value}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </AccordionRow>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default RecommendationsPage
