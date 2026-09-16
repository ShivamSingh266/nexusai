import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FolderKanban,
  Users,
  CheckCircle2,
  Clock,
  ArrowRight,
  Search,
  X,
  ChevronRight,
  Trash2,
  Eye,
  RotateCcw,
  Sparkles,
  AlertCircle,
  GraduationCap,
  Briefcase,
  Calendar,
  Building,
} from 'lucide-react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { StatCard } from '../../components/common/StatCard'
import { MatchScoreBadge } from '../../components/common/MatchScoreBadge'
import { Toast } from '../../components/common/Toast'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { EmptyState } from '../../components/common/EmptyState'
import { SkillChip } from '../../components/common/SkillChip'
import { hiringService } from '../../services/hiringService'
import { cn } from '../../lib/utils'

const STAGES = ['All', 'New', 'Reviewed', 'Interview', 'Selected', 'Rejected']

const NEXT_STAGE_MAP = {
  New: 'Reviewed',
  Reviewed: 'Interview',
  Interview: 'Selected',
}

const SCORE_THRESHOLDS = [
  { label: 'All Scores', value: 0 },
  { label: '75%+ Match', value: 75 },
  { label: '80%+ Match', value: 80 },
  { label: '85%+ Match', value: 85 },
  { label: '90%+ Match', value: 90 },
]

const stageBadgeStyles = {
  New: 'bg-indigo-100 text-indigo-800 border-indigo-200 dark:bg-indigo-950/50 dark:text-indigo-300 dark:border-indigo-800',
  Reviewed: 'bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-950/50 dark:text-amber-300 dark:border-amber-800',
  Interview: 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-950/50 dark:text-blue-300 dark:border-blue-800',
  Selected: 'bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-300 dark:border-emerald-800',
  Rejected: 'bg-rose-100 text-rose-800 border-rose-200 dark:bg-rose-950/50 dark:text-rose-300 dark:border-rose-800',
}

export function ShortlistPage() {
  const navigate = useNavigate()
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  // Filtering states
  const [search, setSearch] = useState('')
  const [selectedStage, setSelectedStage] = useState('All')
  const [selectedRole, setSelectedRole] = useState('All Roles')
  const [minScore, setMinScore] = useState(0)

  // Candidate detail modal state
  const [selectedCandidate, setSelectedCandidate] = useState(null)

  // Toast notifications
  const [toast, setToast] = useState(null)

  // Load shortlist data
  useEffect(() => {
    let isMounted = true
    async function loadShortlist() {
      setError(null)
      try {
        const data = await hiringService.getShortlist()
        if (!isMounted) return
        // Normalize any legacy stage names from mock data to standardized pipeline stages
        const normalized = (data || []).map((c) => ({
          ...c,
          stage: c.stage === 'Shortlisted' ? 'New' : c.stage === 'Review' ? 'Reviewed' : c.stage,
        }))
        setCandidates(normalized)
      } catch (err) {
        if (!isMounted) return
        setError(err?.message || 'Failed to load shortlist candidates.')
      } finally {
        if (isMounted) setLoading(false)
      }
    }
    loadShortlist()
    return () => {
      isMounted = false
    }
  }, [reloadKey])

  // Keyboard close for candidate detail modal
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setSelectedCandidate(null)
      }
    }
    if (selectedCandidate) {
      window.addEventListener('keydown', handleKeyDown)
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [selectedCandidate])

  const handleRetry = () => {
    setLoading(true)
    setReloadKey((prev) => prev + 1)
  }

  // Unique roles present in shortlist
  const availableRoles = useMemo(() => {
    const roles = new Set(candidates.map((c) => c.role).filter(Boolean))
    return ['All Roles', ...Array.from(roles).sort()]
  }, [candidates])

  // Count active filters applied
  const activeFiltersCount = useMemo(() => {
    let count = 0
    if (search.trim()) count++
    if (selectedStage !== 'All') count++
    if (selectedRole !== 'All Roles') count++
    if (minScore > 0) count++
    return count
  }, [search, selectedStage, selectedRole, minScore])

  // Reset all filters
  const handleResetFilters = () => {
    setSearch('')
    setSelectedStage('All')
    setSelectedRole('All Roles')
    setMinScore(0)
  }

  // Filtered candidate list
  const filteredCandidates = useMemo(() => {
    const query = search.toLowerCase().trim()
    return candidates.filter((c) => {
      const matchesStage = selectedStage === 'All' || c.stage === selectedStage
      const matchesRole = selectedRole === 'All Roles' || c.role === selectedRole
      const matchesScore = (c.matchScore || 0) >= minScore

      if (!query) {
        return matchesStage && matchesRole && matchesScore
      }

      const matchesName = c.name?.toLowerCase().includes(query)
      const matchesRoleText = c.role?.toLowerCase().includes(query)
      const matchesDept = c.department?.toLowerCase().includes(query)
      const matchesEducation = c.education?.toLowerCase().includes(query)
      const matchesSkills =
        Array.isArray(c.skills) && c.skills.some((s) => s.toLowerCase().includes(query))

      return (
        matchesStage &&
        matchesRole &&
        matchesScore &&
        (matchesName || matchesRoleText || matchesDept || matchesEducation || matchesSkills)
      )
    })
  }, [candidates, selectedStage, selectedRole, minScore, search])

  // KPI statistics derived from candidate state
  const stats = useMemo(() => {
    const total = candidates.length
    const inInterview = candidates.filter((c) => c.stage === 'Interview').length
    const selected = candidates.filter((c) => c.stage === 'Selected').length
    const reviewed = candidates.filter((c) => c.stage === 'Reviewed' || c.stage === 'New').length
    return { total, inInterview, selected, reviewed }
  }, [candidates])

  // Stage counts for tabs
  const stageCounts = useMemo(() => {
    const counts = { All: candidates.length }
    candidates.forEach((c) => {
      counts[c.stage] = (counts[c.stage] || 0) + 1
    })
    return counts
  }, [candidates])

  // Pipeline stage update
  const handleStageChange = (candidateId, nextStage) => {
    setCandidates((prev) =>
      prev.map((c) => (c.id === candidateId ? { ...c, stage: nextStage } : c)),
    )
    if (selectedCandidate?.id === candidateId) {
      setSelectedCandidate((prev) => (prev ? { ...prev, stage: nextStage } : null))
    }
    const cand = candidates.find((c) => c.id === candidateId)
    setToast({
      variant: 'success',
      title: 'Status Updated',
      message: `${cand?.name || 'Candidate'} moved to "${nextStage}".`,
    })
  }

  // Quick advance to the next pipeline stage
  const handleAdvanceStage = (candidateId) => {
    const cand = candidates.find((c) => c.id === candidateId)
    if (!cand) return
    const nextStage = NEXT_STAGE_MAP[cand.stage]
    if (!nextStage) return
    handleStageChange(candidateId, nextStage)
  }

  // Remove candidate from shortlist
  const handleRemoveCandidate = (candidateId) => {
    const cand = candidates.find((c) => c.id === candidateId)
    setCandidates((prev) => prev.filter((c) => c.id !== candidateId))
    if (selectedCandidate?.id === candidateId) {
      setSelectedCandidate(null)
    }
    setToast({
      variant: 'info',
      title: 'Candidate Removed',
      message: `${cand?.name || 'Candidate'} was removed from the shortlist.`,
    })
  }

  return (
    <div className="space-y-6">
      {toast && (
        <div className="fixed bottom-6 right-6 z-50">
          <Toast
            variant={toast.variant}
            title={toast.title}
            message={toast.message}
            duration={3500}
            onDismiss={() => setToast(null)}
          />
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 dark:border-slate-800 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-600 dark:text-brand-400">
            Hiring
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Shortlisted Candidates
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600 dark:text-slate-400">
            Manage your recruitment funnel stages: review qualified profiles, advance candidates to
            interview, and track offers.
          </p>
        </div>

        <Button
          onClick={() => navigate('/hiring/candidate-matching')}
          className="inline-flex items-center gap-2 self-start md:self-auto"
        >
          <span>Match More Candidates</span>
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Error Alert Banner */}
      {error && (
        <div
          role="alert"
          className="flex items-center justify-between rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300"
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 flex-shrink-0 text-rose-600 dark:text-rose-400" />
            <span>{error}</span>
          </div>
          <Button
            variant="secondary"
            onClick={handleRetry}
            className="h-auto px-3 py-1.5 text-xs font-semibold"
          >
            Retry
          </Button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Total Shortlisted"
          value={stats.total}
          subtitle="Active pipeline"
          loading={loading}
          icon={<FolderKanban className="h-5 w-5 text-brand-600 dark:text-brand-400" />}
        />
        <StatCard
          title="Under Review"
          value={stats.reviewed}
          subtitle="New & reviewed profiles"
          loading={loading}
          icon={<Clock className="h-5 w-5 text-amber-600 dark:text-amber-400" />}
        />
        <StatCard
          title="In Interview"
          value={stats.inInterview}
          subtitle="Scheduled rounds"
          loading={loading}
          icon={<Users className="h-5 w-5 text-blue-600 dark:text-blue-400" />}
        />
        <StatCard
          title="Selected / Offer"
          value={stats.selected}
          subtitle="Offer stage finalists"
          loading={loading}
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />}
        />
      </div>

      {/* Search & Multi-Criteria Filter Bar */}
      <div className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50/90 p-4 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/80">
        {/* Controls Row */}
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          {/* Keyword Search Input */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by candidate name, role, skill, or education..."
              aria-label="Search shortlisted candidates"
              className="w-full rounded-xl border border-slate-200 bg-white py-2 pl-9 pr-9 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-500"
            />
            {search && (
              <button
                type="button"
                onClick={() => setSearch('')}
                aria-label="Clear search input"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Role & Score Filters */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Role Filter */}
            <div className="flex items-center gap-1.5">
              <label htmlFor="role-filter" className="sr-only">
                Filter by Role
              </label>
              <select
                id="role-filter"
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value)}
                className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              >
                {availableRoles.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>
            </div>

            {/* Score Filter */}
            <div className="flex items-center gap-1.5">
              <label htmlFor="score-filter" className="sr-only">
                Filter by Minimum Score
              </label>
              <select
                id="score-filter"
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              >
                {SCORE_THRESHOLDS.map((thresh) => (
                  <option key={thresh.value} value={thresh.value}>
                    {thresh.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Active filter count & Reset button */}
            {activeFiltersCount > 0 && (
              <div className="flex items-center gap-2">
                <span className="rounded-full bg-brand-100 px-2 py-0.5 text-xs font-semibold text-brand-700 dark:bg-brand-950 dark:text-brand-300">
                  {activeFiltersCount} active
                </span>
                <button
                  type="button"
                  onClick={handleResetFilters}
                  className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 transition hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
                >
                  <RotateCcw className="h-3 w-3" />
                  <span>Reset</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Stage Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 border-t border-slate-200/60 pt-1 dark:border-slate-800/60">
          <span className="mr-1 text-xs font-medium text-slate-500 dark:text-slate-400">
            Stages:
          </span>
          {STAGES.map((stg) => {
            const count = stageCounts[stg] || 0
            const isSelected = selectedStage === stg
            return (
              <button
                key={stg}
                type="button"
                aria-pressed={isSelected}
                onClick={() => setSelectedStage(stg)}
                className={cn(
                  'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
                  isSelected
                    ? 'bg-brand-600 text-white shadow-sm dark:bg-brand-500'
                    : 'border border-slate-200 bg-white text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700/60',
                )}
              >
                <span>{stg}</span>
                <span
                  className={cn(
                    'rounded-full px-1.5 py-0.2 text-[10px]',
                    isSelected
                      ? 'bg-white/20 text-white'
                      : 'bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-300',
                  )}
                >
                  {count}
                </span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Pipeline Content */}
      {loading ? (
        <div className="space-y-3">
          <LoadingSkeleton variant="table" className="h-16" />
          <LoadingSkeleton variant="table" className="h-16" />
          <LoadingSkeleton variant="table" className="h-16" />
          <LoadingSkeleton variant="table" className="h-16" />
        </div>
      ) : filteredCandidates.length === 0 ? (
        candidates.length === 0 ? (
          <EmptyState
            title="No Shortlisted Candidates"
            description="Your shortlist is currently empty. Explore qualified profiles in Candidate Matching to review and add top candidates to your pipeline."
            icon="📋"
            actionLabel="Explore Candidate Matching"
            onAction={() => navigate('/hiring/candidate-matching')}
          />
        ) : (
          <EmptyState
            title="No Candidates Match Your Filters"
            description="No shortlisted candidates meet your current search query or filter criteria. Try adjusting or clearing your filters."
            icon="🔍"
            actionLabel="Reset All Filters"
            onAction={handleResetFilters}
          />
        )
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm text-slate-700 dark:text-slate-200">
              <thead className="border-b border-slate-200 bg-slate-50/80 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:border-slate-800 dark:bg-slate-900/80 dark:text-slate-400">
                <tr>
                  <th scope="col" className="px-5 py-3.5">
                    Candidate
                  </th>
                  <th scope="col" className="px-5 py-3.5">
                    Target Role
                  </th>
                  <th scope="col" className="px-5 py-3.5">
                    Match Score
                  </th>
                  <th scope="col" className="hidden px-5 py-3.5 lg:table-cell">
                    Top Skills
                  </th>
                  <th scope="col" className="px-5 py-3.5">
                    Pipeline Stage
                  </th>
                  <th scope="col" className="px-5 py-3.5 text-right">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredCandidates.map((c) => {
                  const nextStage = NEXT_STAGE_MAP[c.stage]
                  return (
                    <tr
                      key={c.id}
                      className="transition hover:bg-slate-50/80 dark:hover:bg-slate-800/50"
                    >
                      {/* Candidate Column */}
                      <td className="px-5 py-4">
                        <div>
                          <button
                            type="button"
                            onClick={() => setSelectedCandidate(c)}
                            className="text-left font-bold text-slate-900 transition hover:text-brand-600 focus:outline-none focus-visible:underline dark:text-white dark:hover:text-brand-400"
                          >
                            {c.name}
                          </button>
                          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                            {c.experience} exp • {c.education} • {c.department}
                          </p>
                        </div>
                      </td>

                      {/* Target Role */}
                      <td className="px-5 py-4 text-xs font-medium text-slate-800 dark:text-slate-200">
                        {c.role}
                      </td>

                      {/* Match Score */}
                      <td className="px-5 py-4">
                        <MatchScoreBadge score={c.matchScore} />
                      </td>

                      {/* Top Skills */}
                      <td className="hidden px-5 py-4 lg:table-cell">
                        <div className="flex flex-wrap items-center gap-1">
                          {(c.skills || []).slice(0, 2).map((s) => (
                            <span
                              key={s}
                              className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300"
                            >
                              {s}
                            </span>
                          ))}
                          {(c.skills || []).length > 2 && (
                            <span className="text-[10px] text-slate-400 dark:text-slate-500">
                              +{(c.skills || []).length - 2} more
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Pipeline Stage */}
                      <td className="px-5 py-4">
                        <span
                          className={cn(
                            'inline-flex rounded-full border px-2.5 py-0.5 text-xs font-semibold',
                            stageBadgeStyles[c.stage] ||
                              'border-slate-200 bg-slate-100 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300',
                          )}
                        >
                          {c.stage}
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="px-5 py-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {/* View Profile Button */}
                          <button
                            type="button"
                            onClick={() => setSelectedCandidate(c)}
                            aria-label={`View ${c.name}'s profile details`}
                            title="View Full Profile Dossier"
                            className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-brand-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-brand-400"
                          >
                            <Eye className="h-4 w-4" />
                          </button>

                          {/* Quick Advance Button */}
                          {nextStage ? (
                            <button
                              type="button"
                              onClick={() => handleAdvanceStage(c.id)}
                              aria-label={`Advance ${c.name} to ${nextStage}`}
                              title={`Advance candidate to ${nextStage}`}
                              className="inline-flex items-center gap-1 rounded-lg bg-brand-50 px-2.5 py-1 text-xs font-semibold text-brand-700 transition hover:bg-brand-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:bg-brand-950/60 dark:text-brand-300 dark:hover:bg-brand-900/60"
                            >
                              <span>Advance</span>
                              <ChevronRight className="h-3 w-3" />
                            </button>
                          ) : c.stage === 'Selected' ? (
                            <span className="px-2 py-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                              Selected
                            </span>
                          ) : (
                            <span className="px-2 py-1 text-[11px] font-semibold text-rose-500 dark:text-rose-400">
                              Rejected
                            </span>
                          )}

                          {/* Direct Stage Selector Dropdown */}
                          <select
                            value={c.stage}
                            onChange={(e) => handleStageChange(c.id, e.target.value)}
                            aria-label={`Change stage for ${c.name}`}
                            className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                          >
                            <option value="New">New</option>
                            <option value="Reviewed">Reviewed</option>
                            <option value="Interview">Interview</option>
                            <option value="Selected">Selected</option>
                            <option value="Rejected">Rejected</option>
                          </select>

                          {/* Remove from Shortlist Button */}
                          <button
                            type="button"
                            onClick={() => handleRemoveCandidate(c.id)}
                            aria-label={`Remove ${c.name} from shortlist`}
                            title="Remove from Shortlist"
                            className="rounded-lg p-1.5 text-slate-400 transition hover:bg-rose-50 hover:text-rose-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-500 dark:text-slate-500 dark:hover:bg-rose-950/40 dark:hover:text-rose-400"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Candidate Profile Dossier Modal */}
      {selectedCandidate && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="dossier-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm"
          onClick={(e) => {
            if (e.target === e.currentTarget) setSelectedCandidate(null)
          }}
        >
          <div className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900 sm:p-8">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-slate-100 pb-5 dark:border-slate-800">
              <div>
                <div className="flex items-center gap-3">
                  <h2
                    id="dossier-title"
                    className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white"
                  >
                    {selectedCandidate.name}
                  </h2>
                  <MatchScoreBadge score={selectedCandidate.matchScore} />
                </div>
                <p className="mt-1 text-sm font-medium text-brand-600 dark:text-brand-400">
                  {selectedCandidate.role} • {selectedCandidate.department}
                </p>
              </div>

              <button
                type="button"
                onClick={() => setSelectedCandidate(null)}
                aria-label="Close candidate profile modal"
                className="rounded-xl p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:text-slate-500 dark:hover:bg-slate-800 dark:hover:text-slate-300"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="mt-6 space-y-6">
              {/* AI Match Evaluation */}
              <div className="rounded-2xl border border-brand-200/70 bg-brand-50/50 p-4.5 dark:border-brand-900/40 dark:bg-brand-950/30">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-brand-700 dark:text-brand-300">
                  <Sparkles className="h-4 w-4" />
                  <span>AI Match Rationale</span>
                </div>
                <p className="mt-2 text-sm leading-relaxed text-slate-700 dark:text-slate-300">
                  {selectedCandidate.summary}
                </p>
                {selectedCandidate.reason && (
                  <p className="mt-2 border-t border-brand-200/50 pt-2 text-xs italic text-brand-900/80 dark:border-brand-900/40 dark:text-brand-300/80">
                    “{selectedCandidate.reason}”
                  </p>
                )}
              </div>

              {/* Profile Details Grid */}
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div className="rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-800/60">
                  <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                    <Briefcase className="h-3.5 w-3.5" />
                    <span>Experience</span>
                  </div>
                  <p className="mt-1 font-semibold text-slate-800 dark:text-slate-200">
                    {selectedCandidate.experience}
                  </p>
                </div>

                <div className="rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-800/60">
                  <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                    <GraduationCap className="h-3.5 w-3.5" />
                    <span>Education</span>
                  </div>
                  <p className="mt-1 font-semibold text-slate-800 dark:text-slate-200">
                    {selectedCandidate.education}
                  </p>
                </div>

                <div className="rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-800/60">
                  <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                    <Building className="h-3.5 w-3.5" />
                    <span>Department</span>
                  </div>
                  <p className="mt-1 font-semibold text-slate-800 dark:text-slate-200">
                    {selectedCandidate.department}
                  </p>
                </div>

                <div className="rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-800/60">
                  <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                    <Calendar className="h-3.5 w-3.5" />
                    <span>Shortlisted</span>
                  </div>
                  <p className="mt-1 text-xs font-semibold text-slate-800 dark:text-slate-200">
                    {selectedCandidate.dateShortlisted}
                  </p>
                </div>
              </div>

              {/* Skills List */}
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Verified Skills
                </h3>
                <div className="mt-2.5 flex flex-wrap gap-2">
                  {(selectedCandidate.skills || []).map((skill) => (
                    <SkillChip key={skill} skill={skill} />
                  ))}
                </div>
              </div>

              {/* Pipeline Actions Footer */}
              <div className="border-t border-slate-100 pt-5 dark:border-slate-800">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                      Current Stage:
                    </span>
                    <span
                      className={cn(
                        'inline-flex rounded-full border px-2.5 py-0.5 text-xs font-semibold',
                        stageBadgeStyles[selectedCandidate.stage],
                      )}
                    >
                      {selectedCandidate.stage}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    {/* Stage Selector in Modal */}
                    <select
                      value={selectedCandidate.stage}
                      onChange={(e) => handleStageChange(selectedCandidate.id, e.target.value)}
                      aria-label="Change stage in profile modal"
                      className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                    >
                      <option value="New">New</option>
                      <option value="Reviewed">Reviewed</option>
                      <option value="Interview">Interview</option>
                      <option value="Selected">Selected</option>
                      <option value="Rejected">Rejected</option>
                    </select>

                    {/* Quick Advance Button in Modal */}
                    {NEXT_STAGE_MAP[selectedCandidate.stage] && (
                      <Button
                        variant="primary"
                        onClick={() => handleAdvanceStage(selectedCandidate.id)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 text-xs"
                      >
                        <span>Advance to {NEXT_STAGE_MAP[selectedCandidate.stage]}</span>
                        <ChevronRight className="h-3.5 w-3.5" />
                      </Button>
                    )}

                    {/* Remove from Shortlist in Modal */}
                    <button
                      type="button"
                      onClick={() => handleRemoveCandidate(selectedCandidate.id)}
                      className="inline-flex items-center gap-1 rounded-full border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-600 transition hover:bg-rose-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-500 dark:border-rose-900/50 dark:text-rose-400 dark:hover:bg-rose-950/40"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      <span>Remove</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ShortlistPage
