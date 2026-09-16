import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Briefcase,
  Users,
  UserCheck,
  FolderKanban,
  Plus,
  ArrowRight,
  Sparkles,
  Building2,
  AlertTriangle,
  RotateCcw,
  MapPin,
  Clock,
  ChevronRight,
} from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StatCard } from '../../components/common/StatCard'
import { StatusBadge } from '../../components/hiring/StatusBadge'
import { MatchScoreBadge } from '../../components/common/MatchScoreBadge'
import { SkillChip } from '../../components/common/SkillChip'
import { PriorityTag } from '../../components/common/PriorityTag'
import { TrendArrow } from '../../components/common/TrendArrow'
import { LineTrendChart } from '../../components/charts/LineTrendChart'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { EmptyState } from '../../components/common/EmptyState'
import { hiringService } from '../../services/hiringService'
import { hiringKpis } from '../../mocks/hiringMockData'

export function HiringDashboardPage() {
  const navigate = useNavigate()
  const [jobs, setJobs] = useState([])
  const [candidates, setCandidates] = useState([])
  const [shortlist, setShortlist] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [refreshIndex, setRefreshIndex] = useState(0)

  useEffect(() => {
    let ignore = false

    async function load() {
      try {
        const [jobsRes, candidatesRes, shortlistRes] = await Promise.all([
          hiringService.getJobs(),
          hiringService.getCandidates(),
          hiringService.getShortlist(),
        ])
        if (!ignore) {
          setJobs(jobsRes?.data || [])
          setCandidates(candidatesRes || [])
          setShortlist(shortlistRes || [])
        }
      } catch (err) {
        if (!ignore) {
          setError(err?.message || 'Failed to load hiring dashboard data. Please check your connection.')
        }
      } finally {
        if (!ignore) {
          setLoading(false)
        }
      }
    }

    load()

    return () => {
      ignore = true
    }
  }, [refreshIndex])

  const handleRetry = () => {
    setLoading(true)
    setError(null)
    setRefreshIndex((prev) => prev + 1)
  }

  // Recruiter quick action items linking to established routes
  const recruiterActions = [
    {
      label: 'Post a Job',
      description: 'Create and publish open requisitions',
      path: '/hiring/post-job',
      icon: Briefcase,
      badge: 'Requisition',
      color: 'text-brand-600 dark:text-brand-400',
      bg: 'bg-brand-50 dark:bg-brand-950/40 border-brand-100 dark:border-brand-900/40',
    },
    {
      label: 'Candidate Matching',
      description: 'AI semantic matching & scoring',
      path: '/hiring/candidate-matching',
      icon: Sparkles,
      badge: 'AI Powered',
      color: 'text-indigo-600 dark:text-indigo-400',
      bg: 'bg-indigo-50 dark:bg-indigo-950/40 border-indigo-100 dark:border-indigo-900/40',
    },
    {
      label: 'Talent Shortlist',
      description: 'Pipeline review & stage decisions',
      path: '/hiring/shortlist',
      icon: FolderKanban,
      badge: `${shortlist.length || 5} queued`,
      color: 'text-violet-600 dark:text-violet-400',
      bg: 'bg-violet-50 dark:bg-violet-950/40 border-violet-100 dark:border-violet-900/40',
    },
    {
      label: 'Company Profile',
      description: 'Organization identity & branding',
      path: '/hiring/company-profile',
      icon: Building2,
      badge: 'Profile',
      color: 'text-emerald-600 dark:text-emerald-400',
      bg: 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-100 dark:border-emerald-900/40',
    },
  ]

  // Hiring momentum trend trajectory data
  const recruitmentTrend = [
    { label: 'W1', value: 18 },
    { label: 'W2', value: 24 },
    { label: 'W3', value: 31 },
    { label: 'W4', value: 42 },
    { label: 'W5', value: 58 },
    { label: 'W6', value: 74 },
  ]

  // Match count helper per job based on candidateMatchData
  const getJobMatchCount = (job) => {
    if (!candidates || candidates.length === 0) return 0
    const matched = candidates.filter((c) => {
      if (job.id && c.jobId === job.id) return true
      if (job.title && c.targetRole && c.targetRole.toLowerCase() === job.title.toLowerCase()) return true
      return false
    })
    return matched.length || 2
  }

  return (
    <div className="space-y-6">
      {/* Recruiter Header */}
      <header className="flex flex-col gap-4 border-b border-slate-200 pb-6 dark:border-slate-800 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-brand-700 dark:bg-brand-950/50 dark:text-brand-300">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Hiring Portal</span>
          </div>
          <h1 className="mt-2 text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Hiring Dashboard
          </h1>
          <p className="mt-1.5 max-w-2xl text-sm leading-relaxed text-slate-600 dark:text-slate-400">
            Manage active job requisitions, evaluate AI-matched candidates, track your talent shortlist pipeline, and accelerate hiring decisions.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button
            variant="secondary"
            onClick={() => navigate('/hiring/candidate-matching')}
            className="inline-flex items-center gap-2 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          >
            <Users className="h-4 w-4 text-brand-600 dark:text-brand-400" />
            <span>Candidate Matching</span>
          </Button>

          <Button
            onClick={() => navigate('/hiring/post-job')}
            className="inline-flex items-center gap-2 shadow-sm"
          >
            <Plus className="h-4 w-4" />
            <span>Post a Job</span>
          </Button>
        </div>
      </header>

      {/* Error Banner with Retry */}
      {error && (
        <div
          role="alert"
          className="flex items-center justify-between rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-200"
        >
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-rose-600 shrink-0 dark:text-rose-400" />
            <div>
              <p className="font-semibold">Unable to load complete dashboard data</p>
              <p className="text-xs opacity-90">{error}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleRetry}
            className="inline-flex items-center gap-1.5 rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-rose-700 dark:bg-rose-700 dark:hover:bg-rose-600"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* KPI / Overview Section */}
      <section aria-label="Recruiter Key Metrics" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {loading ? (
          <>
            <LoadingSkeleton variant="card" />
            <LoadingSkeleton variant="card" />
            <LoadingSkeleton variant="card" />
            <LoadingSkeleton variant="card" />
          </>
        ) : (
          <>
            <StatCard
              title="Active Jobs"
              value={jobs.length > 0 ? String(jobs.length) : hiringKpis[0]?.value || '18'}
              subtitle={hiringKpis[0]?.change || '+3 this month'}
              icon={<Briefcase className="h-5 w-5 text-brand-600 dark:text-brand-400" />}
              trend="+3 this month"
            />
            <StatCard
              title="Total Candidates"
              value={hiringKpis[1]?.value || '2,438'}
              subtitle="Talent pool intake"
              icon={<Users className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />}
              trend="+12.4%"
            />
            <StatCard
              title="Candidates Matched"
              value={candidates.length > 0 ? String(candidates.length) : '5'}
              subtitle="High confidence (>=75%)"
              icon={<UserCheck className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />}
              trend="+94% peak"
            />
            <StatCard
              title="Shortlisted Pipeline"
              value={shortlist.length > 0 ? String(shortlist.length) : hiringKpis[2]?.value || '486'}
              subtitle={hiringKpis[2]?.change || '+18 new'}
              icon={<FolderKanban className="h-5 w-5 text-violet-600 dark:text-violet-400" />}
              trend="+18 new"
            />
          </>
        )}
      </section>

      {/* Main Grid: Active Jobs (Left) & Quick Actions / Velocity (Right) */}
      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        {/* Active Jobs Section */}
        <section aria-label="Active Job Postings" className="space-y-6">
          <Card className="overflow-hidden border border-slate-200 dark:border-slate-800">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4 dark:border-slate-800">
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">Active Job Postings</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">Live roles, applicant intake, and AI candidate matching</p>
              </div>
              <Button
                variant="secondary"
                onClick={() => navigate('/hiring/post-job')}
                className="px-3 py-1.5 text-xs font-semibold dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
              >
                <Plus className="mr-1 h-3.5 w-3.5" />
                <span>Add Job</span>
              </Button>
            </div>

            {loading ? (
              <div className="space-y-3 p-5">
                <LoadingSkeleton variant="table" />
                <LoadingSkeleton variant="table" />
                <LoadingSkeleton variant="table" />
              </div>
            ) : jobs.length === 0 ? (
              <div className="p-6">
                <EmptyState
                  title="No active job requisitions"
                  description="Post your first role to start semantic AI candidate matching and candidate reviews."
                  actionLabel="Post a Job"
                  onAction={() => navigate('/hiring/post-job')}
                />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm text-slate-700 dark:text-slate-300">
                  <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:bg-slate-800/50 dark:border-slate-800 dark:text-slate-400">
                    <tr>
                      <th scope="col" className="px-5 py-3.5">Job Title</th>
                      <th scope="col" className="px-5 py-3.5">Department</th>
                      <th scope="col" className="px-5 py-3.5">Status</th>
                      <th scope="col" className="px-5 py-3.5">Applicants</th>
                      <th scope="col" className="px-5 py-3.5">AI Matches</th>
                      <th scope="col" className="px-5 py-3.5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {jobs.slice(0, 5).map((job, idx) => (
                      <tr
                        key={job.id || `${job.title}-${idx}`}
                        className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition"
                      >
                        <td className="px-5 py-4">
                          <div>
                            <p className="font-bold text-slate-900 dark:text-slate-100">{job.title}</p>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                              {job.postedDate ? `Posted ${job.postedDate}` : job.location || 'Full-time'}
                            </p>
                          </div>
                        </td>

                        <td className="px-5 py-4 text-xs font-medium text-slate-600 dark:text-slate-300">
                          {job.department || 'Engineering'}
                        </td>

                        <td className="px-5 py-4">
                          <StatusBadge status={job.status || 'Hiring'} />
                        </td>

                        <td className="px-5 py-4">
                          <span className="inline-flex items-center gap-1 font-semibold text-xs text-slate-900 dark:text-slate-100">
                            <Users className="h-3.5 w-3.5 text-brand-600 dark:text-brand-400" />
                            <span>{job.applicants ?? 48}</span>
                          </span>
                        </td>

                        <td className="px-5 py-4">
                          <span className="inline-flex items-center gap-1 rounded-full bg-indigo-50 dark:bg-indigo-950/50 px-2 py-0.5 text-xs font-semibold text-indigo-700 dark:text-indigo-300 border border-indigo-100 dark:border-indigo-900/50">
                            <Sparkles className="h-3 w-3 text-indigo-600 dark:text-indigo-400" />
                            <span>{getJobMatchCount(job)} matches</span>
                          </span>
                        </td>

                        <td className="px-5 py-4 text-right">
                          <button
                            type="button"
                            onClick={() => navigate('/hiring/candidate-matching')}
                            className="inline-flex items-center gap-1 text-xs font-semibold text-brand-700 hover:text-brand-800 dark:text-brand-400 dark:hover:text-brand-300 transition"
                          >
                            <span>Match Candidates</span>
                            <ArrowRight className="h-3 w-3" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/20 px-5 py-3 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
              <span>Showing {jobs.slice(0, 5).length} of {jobs.length || 4} active positions</span>
              <button
                type="button"
                onClick={() => navigate('/hiring/candidate-matching')}
                className="font-semibold text-brand-700 hover:text-brand-800 dark:text-brand-400 dark:hover:text-brand-300"
              >
                View all candidate matches →
              </button>
            </div>
          </Card>

          {/* Top Candidate Matches Preview */}
          <Card className="p-5 border border-slate-200 dark:border-slate-800">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-4 pb-3 border-b border-slate-100 dark:border-slate-800">
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">Top Candidate Matches</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">AI-ranked profiles ready for recruiter evaluation and screening</p>
              </div>
              <button
                type="button"
                onClick={() => navigate('/hiring/candidate-matching')}
                className="inline-flex items-center gap-1 text-xs font-semibold text-brand-700 hover:text-brand-800 dark:text-brand-400 dark:hover:text-brand-300"
              >
                <span>Full AI Matching</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>

            {loading ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <LoadingSkeleton variant="card" />
                <LoadingSkeleton variant="card" />
              </div>
            ) : candidates.length === 0 ? (
              <EmptyState
                title="No matched candidates yet"
                description="Once candidates apply or are imported, their semantic competency score will show here."
                actionLabel="Explore Roles"
                onAction={() => navigate('/hiring/post-job')}
              />
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                {candidates.slice(0, 4).map((c) => (
                  <div
                    key={c.id}
                    className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-slate-50/60 p-4 transition hover:border-brand-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-800/40 dark:hover:border-slate-700 dark:hover:bg-slate-800/70"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">{c.name}</h3>
                            {c.priority && <PriorityTag priority={c.priority} />}
                          </div>
                          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                            {c.targetRole || c.currentRole} • {c.experience}
                          </p>
                        </div>
                        <MatchScoreBadge score={c.score} />
                      </div>

                      {/* Verified competencies / skills */}
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {c.skills?.slice(0, 3).map((skill) => (
                          <SkillChip key={skill} skill={skill} variant="default" />
                        ))}
                        {c.skills && c.skills.length > 3 && (
                          <span className="self-center text-[10px] font-semibold text-slate-400">
                            +{c.skills.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="mt-4 flex items-center justify-between border-t border-slate-200/60 pt-3 text-xs text-slate-500 dark:border-slate-800 dark:text-slate-400">
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3 w-3 text-slate-400" />
                        {c.location || 'Remote'}
                      </span>
                      <button
                        type="button"
                        onClick={() => navigate('/hiring/candidate-matching')}
                        className="font-semibold text-brand-700 hover:text-brand-800 dark:text-brand-400 dark:hover:text-brand-300"
                      >
                        Evaluate Match →
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </section>

        {/* Right Column: Quick Actions, Velocity Chart, Shortlist Activity */}
        <aside aria-label="Recruiter Operations" className="space-y-6">
          {/* Quick Actions Card */}
          <Card className="p-5 border border-slate-200 dark:border-slate-800">
            <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">Recruiter Quick Actions</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">Direct shortcuts to critical recruitment tools</p>

            <div className="grid gap-3">
              {recruiterActions.map((action) => {
                const ActionIcon = action.icon
                return (
                  <button
                    key={action.label}
                    type="button"
                    onClick={() => navigate(action.path)}
                    className="group flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3 text-left transition hover:border-brand-300 hover:bg-brand-50/40 dark:border-slate-800 dark:bg-slate-900/60 dark:hover:border-slate-700 dark:hover:bg-slate-800/60"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border ${action.bg} ${action.color}`}>
                        <ActionIcon className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-semibold text-slate-900 group-hover:text-brand-700 dark:text-slate-100 dark:group-hover:text-brand-400 transition">
                            {action.label}
                          </p>
                          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                            {action.badge}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{action.description}</p>
                      </div>
                    </div>

                    <ChevronRight className="h-4 w-4 text-slate-400 group-hover:translate-x-0.5 group-hover:text-brand-600 transition" />
                  </button>
                )
              })}
            </div>
          </Card>

          {/* Hiring Momentum / Velocity Chart */}
          <Card className="p-5 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">Recruitment Velocity</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">Weekly candidate intake trajectory</p>
              </div>
              <TrendArrow direction="up" percentage={28} />
            </div>
            <LineTrendChart data={recruitmentTrend} height={130} strokeColor="#4f46e5" fillColor="#6366f1" />
          </Card>

          {/* Shortlist Pipeline Activity */}
          <Card className="p-5 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100 dark:border-slate-800">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">Recent Shortlist</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">Active candidates in hiring funnel</p>
              </div>
              <button
                type="button"
                onClick={() => navigate('/hiring/shortlist')}
                className="text-xs font-semibold text-brand-700 hover:text-brand-800 dark:text-brand-400 dark:hover:text-brand-300"
              >
                View Pipeline →
              </button>
            </div>

            {loading ? (
              <div className="space-y-2.5">
                <LoadingSkeleton variant="list" />
                <LoadingSkeleton variant="list" />
              </div>
            ) : shortlist.length === 0 ? (
              <EmptyState
                title="No shortlisted candidates"
                description="Shortlist qualified candidates from the matching screen to track them here."
                actionLabel="Match Candidates"
                onAction={() => navigate('/hiring/candidate-matching')}
              />
            ) : (
              <div className="space-y-3">
                {shortlist.slice(0, 3).map((candidate) => (
                  <div
                    key={candidate.id}
                    className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/50 p-3 dark:border-slate-800/80 dark:bg-slate-800/30"
                  >
                    <div className="min-w-0 pr-2">
                      <p className="truncate text-xs font-bold text-slate-900 dark:text-slate-100">
                        {candidate.name}
                      </p>
                      <p className="truncate text-[11px] text-slate-500 dark:text-slate-400">
                        {candidate.role}
                      </p>
                      <div className="mt-1 flex items-center gap-2 text-[10px] text-slate-400">
                        <span className="flex items-center gap-1">
                          <Clock className="h-2.5 w-2.5" />
                          {candidate.dateShortlisted || 'Recent'}
                        </span>
                        <span className="rounded-full bg-brand-100 dark:bg-brand-900/50 px-1.5 py-0.2 text-brand-700 dark:text-brand-300 font-medium">
                          {candidate.stage || 'Review'}
                        </span>
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-1.5 shrink-0">
                      <MatchScoreBadge score={candidate.matchScore || 85} />
                      <button
                        type="button"
                        onClick={() => navigate('/hiring/shortlist')}
                        className="text-[11px] font-semibold text-brand-700 hover:text-brand-800 dark:text-brand-400"
                      >
                        Manage
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </aside>
      </div>
    </div>
  )
}

export default HiringDashboardPage
