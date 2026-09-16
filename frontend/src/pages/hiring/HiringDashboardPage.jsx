import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Briefcase, Users, UserCheck, TrendingUp, Plus, ArrowRight } from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StatCard } from '../../components/common/StatCard'
import { MatchScoreBadge } from '../../components/common/MatchScoreBadge'
import { TrendArrow } from '../../components/common/TrendArrow'
import { LineTrendChart } from '../../components/charts/LineTrendChart'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { EmptyState } from '../../components/common/EmptyState'
import { hiringService } from '../../services/hiringService'
import { hiringKpis, quickActions, recentCandidates } from '../../mocks/hiringMockData'

export function HiringDashboardPage() {
  const navigate = useNavigate()
  const [jobs, setJobs] = useState([])
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const [jobsRes, candidatesRes] = await Promise.all([
          hiringService.getJobs(),
          hiringService.getCandidates(),
        ])
        setJobs(jobsRes?.data || [])
        setCandidates(candidatesRes || [])
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const kpiIcons = [
    <Briefcase key="1" className="h-5 w-5 text-brand-600" />,
    <Users key="2" className="h-5 w-5 text-indigo-600" />,
    <UserCheck key="3" className="h-5 w-5 text-emerald-600" />,
    <TrendingUp key="4" className="h-5 w-5 text-amber-600" />,
  ]

  // Hiring momentum trend data
  const recruitmentTrend = [
    { label: 'W1', value: 18 },
    { label: 'W2', value: 24 },
    { label: 'W3', value: 31 },
    { label: 'W4', value: 42 },
    { label: 'W5', value: 58 },
    { label: 'W6', value: 74 },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Hiring</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Recruiter Command Center</h1>
          <p className="mt-2 max-w-xl text-sm text-slate-600">
            Track active job postings, evaluate incoming candidate matches, manage your shortlist, and accelerate hiring cycles.
          </p>
        </div>

        <Button onClick={() => navigate('/hiring/post-job')} className="inline-flex items-center gap-2">
          <Plus className="h-4 w-4" />
          <span>Post a Job</span>
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
          hiringKpis.map((item, index) => (
            <StatCard
              key={item.label}
              title={item.label}
              value={item.value}
              subtitle={item.change}
              icon={kpiIcons[index % kpiIcons.length]}
              trend={item.change.startsWith('+') ? item.change : undefined}
            />
          ))
        )}
      </section>

      {/* Active Jobs & Quick Actions */}
      <section className="grid gap-6 xl:grid-cols-[1.5fr_0.9fr]">
        <Card className="overflow-hidden">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Active Job Postings</h2>
              <p className="text-xs text-slate-500">Live roles and applicant momentum</p>
            </div>
            <Button
              variant="secondary"
              onClick={() => navigate('/hiring/post-job')}
              className="px-3 py-1.5 text-xs"
            >
              Add Job
            </Button>
          </div>

          {loading ? (
            <div className="p-4 space-y-3">
              <LoadingSkeleton variant="table" />
              <LoadingSkeleton variant="table" />
            </div>
          ) : jobs.length === 0 ? (
            <div className="p-6">
              <EmptyState
                title="No active jobs"
                description="Post your first open position to start matching candidates."
                actionLabel="Post a Job"
                onAction={() => navigate('/hiring/post-job')}
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-700">
                <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <tr>
                    <th className="px-5 py-3">Job Title</th>
                    <th className="px-5 py-3">Department</th>
                    <th className="px-5 py-3">Applicants</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {jobs.slice(0, 5).map((job) => (
                    <tr key={job.id || job.title} className="hover:bg-slate-50/80 transition">
                      <td className="px-5 py-3.5 font-semibold text-slate-900">{job.title}</td>
                      <td className="px-5 py-3.5 text-xs text-slate-600">{job.department}</td>
                      <td className="px-5 py-3.5 text-xs font-bold text-brand-700">
                        {job.applicants ?? 0} applied
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="inline-flex rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
                          {job.status || 'Active'}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button
                          type="button"
                          onClick={() => navigate('/hiring/candidate-matching')}
                          className="text-xs font-semibold text-brand-700 hover:text-brand-800"
                        >
                          View Matches →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* Quick Actions & Shortlist Stats */}
        <div className="space-y-6">
          <Card className="p-5">
            <h2 className="text-lg font-semibold text-slate-900 mb-1">Recruiter Shortcuts</h2>
            <p className="text-xs text-slate-500 mb-4">Direct links to candidate pipelines</p>

            <div className="grid gap-3">
              {quickActions.map((action) => (
                <button
                  key={action.label}
                  type="button"
                  onClick={() => action.path && navigate(action.path)}
                  className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50/70 px-4 py-3 text-left transition hover:border-brand-200 hover:bg-brand-50/50"
                >
                  <div>
                    <div className="text-sm font-semibold text-slate-900">{action.label}</div>
                    <div className="text-xs text-slate-500">{action.value}</div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-slate-400" />
                </button>
              ))}
            </div>
          </Card>

          {/* Hiring Momentum Trend */}
          <Card className="p-5">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Application Velocity</h3>
                <p className="text-xs text-slate-500">Weekly applicant intake curve</p>
              </div>
              <TrendArrow direction="up" percentage={28} />
            </div>
            <LineTrendChart data={recruitmentTrend} height={130} strokeColor="#4f46e5" fillColor="#6366f1" />
          </Card>
        </div>
      </section>

      {/* Top Candidate Matches Preview */}
      <Card className="p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Top Candidate Matches</h2>
            <p className="text-xs text-slate-500">AI-ranked candidates ready for recruiter review</p>
          </div>
          <button
            type="button"
            onClick={() => navigate('/hiring/candidate-matching')}
            className="text-xs font-semibold text-brand-700 hover:text-brand-800"
          >
            See All Candidates →
          </button>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {candidates.slice(0, 4).map((c) => (
            <div
              key={c.id}
              className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4 hover:border-brand-300 transition"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h4 className="font-bold text-sm text-slate-900">{c.name}</h4>
                  <p className="text-xs text-slate-500">{c.experience}</p>
                </div>
                <MatchScoreBadge score={c.score} />
              </div>

              <div className="mt-3 flex flex-wrap gap-1">
                {c.skills.slice(0, 3).map((s) => (
                  <span key={s} className="rounded bg-white border border-slate-200 px-1.5 py-0.5 text-[10px] text-slate-600 font-medium">
                    {s}
                  </span>
                ))}
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-xs text-slate-500">{c.location}</span>
                <button
                  type="button"
                  onClick={() => navigate('/hiring/candidate-matching')}
                  className="text-xs font-semibold text-brand-700 hover:text-brand-800"
                >
                  Review
                </button>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

export default HiringDashboardPage
