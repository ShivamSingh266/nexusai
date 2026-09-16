import { useEffect, useState } from 'react'
import { Sparkles, TrendingUp, Compass, ArrowUpRight } from 'lucide-react'
import { Card } from '../../components/ui/Card'
import { PriorityTag } from '../../components/common/PriorityTag'
import { TrendArrow } from '../../components/common/TrendArrow'
import { ProgressRing } from '../../components/charts/ProgressRing'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { governmentService } from '../../services/governmentService'

export function EmergingSkillsPage() {
  const [emergingSkills, setEmergingSkills] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const data = await governmentService.getEmergingSkills()
        setEmergingSkills(data)
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
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Emerging & High-Growth Skills</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
          Identify early-stage technological signals and competencies undergoing rapid demand acceleration across public and private sectors.
        </p>
      </div>

      {/* Grid of Emerging Skills Cards */}
      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <LoadingSkeleton variant="card" />
          <LoadingSkeleton variant="card" />
          <LoadingSkeleton variant="card" />
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {emergingSkills.map((skill) => (
            <Card key={skill.name} className="p-5 flex flex-col justify-between hover:shadow-md transition-shadow">
              <div>
                {/* Header with Title and Priority Tag */}
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-1.5 text-xs text-brand-600 font-semibold mb-1">
                      <Sparkles className="h-3.5 w-3.5" />
                      <span>Emerging Competency</span>
                    </div>
                    <h2 className="text-lg font-bold text-slate-900">{skill.name}</h2>
                  </div>

                  <PriorityTag priority={skill.priority} />
                </div>

                {/* Progress Ring & Growth Stats */}
                <div className="mt-4 flex items-center justify-between rounded-xl bg-slate-50 p-3.5 border border-slate-100">
                  <div className="flex items-center gap-3">
                    <ProgressRing
                      percentage={skill.demand}
                      size={54}
                      strokeWidth={6}
                      color="#2563eb"
                      showValue={true}
                    />
                    <div>
                      <p className="text-[11px] font-medium text-slate-500">Current Demand</p>
                      <p className="text-sm font-bold text-slate-800">{skill.demand}/100</p>
                    </div>
                  </div>

                  <div className="text-right">
                    <p className="text-[11px] font-medium text-slate-500">Acceleration</p>
                    <div className="text-sm font-bold">
                      <TrendArrow direction="up" percentage={skill.growth} />
                    </div>
                  </div>
                </div>

                {/* Affected Sectors and Affected Regions */}
                <div className="mt-4 space-y-2 text-xs">
                  <div className="flex items-center justify-between text-slate-600">
                    <span className="font-medium text-slate-500">Affected Sector:</span>
                    <span className="font-semibold text-slate-800">{skill.sector}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-600">
                    <span className="font-medium text-slate-500">Primary Region:</span>
                    <span className="inline-flex items-center gap-1 font-semibold text-slate-800">
                      <Compass className="h-3 w-3 text-slate-400" />
                      {skill.region}
                    </span>
                  </div>
                </div>
              </div>

              {/* Policy Action Recommendation */}
              <div className="mt-5 rounded-xl border border-brand-100 bg-brand-50/60 p-3">
                <p className="text-[10px] uppercase tracking-wider font-bold text-brand-700">Recommended Policy Action</p>
                <p className="mt-1 text-xs text-brand-900 leading-relaxed">{skill.action}</p>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

export default EmergingSkillsPage
