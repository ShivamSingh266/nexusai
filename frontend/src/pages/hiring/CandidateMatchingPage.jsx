import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Filter,
  MapPin,
  Clock,
  CheckCircle,
  ChevronRight,
  Search,
  RotateCcw,
  AlertTriangle,
  Sparkles,
  UserCheck,
  UserPlus,
  X,
} from 'lucide-react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { MatchScoreBadge } from '../../components/common/MatchScoreBadge'
import { SkillChip } from '../../components/common/SkillChip'
import { PriorityTag } from '../../components/common/PriorityTag'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { EmptyState } from '../../components/common/EmptyState'
import { Toast } from '../../components/common/Toast'
import { hiringService } from '../../services/hiringService'

export function CandidateMatchingPage() {
  const navigate = useNavigate()
  const [jobs, setJobs] = useState([])
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [refreshIndex, setRefreshIndex] = useState(0)

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedJob, setSelectedJob] = useState('all-jobs')
  const [selectedSkill, setSelectedSkill] = useState('All')
  const [selectedExperience, setSelectedExperience] = useState('All')
  const [selectedLocation, setSelectedLocation] = useState('All')
  const [selectedMinScore, setSelectedMinScore] = useState('All')
  const [selectedAvailability, setSelectedAvailability] = useState('All')

  const [selectedCandidateId, setSelectedCandidateId] = useState(null)
  const [shortlistedIds, setShortlistedIds] = useState(() => new Set())
  const [toast, setToast] = useState(null)

  useEffect(() => {
    let ignore = false

    async function loadData() {
      try {
        const [jobsData, candidatesData] = await Promise.all([
          hiringService.getJobOptions(),
          hiringService.getCandidates(),
        ])
        if (!ignore) {
          setJobs(jobsData || [])
          setCandidates(candidatesData || [])
          if (candidatesData?.length > 0) {
            setSelectedCandidateId(candidatesData[0].id)
          }
        }
      } catch (err) {
        if (!ignore) {
          setError(err?.message || 'Failed to load candidates. Please check your connection.')
        }
      } finally {
        if (!ignore) {
          setLoading(false)
        }
      }
    }

    loadData()

    return () => {
      ignore = true
    }
  }, [refreshIndex])

  const handleRetry = () => {
    setLoading(true)
    setError(null)
    setRefreshIndex((prev) => prev + 1)
  }

  // Collect unique filter options from candidates
  const allSkills = useMemo(() => {
    return ['All', ...new Set(candidates.flatMap((c) => c.skills || []))]
  }, [candidates])

  const allLocations = useMemo(() => {
    return ['All', ...new Set(candidates.map((c) => c.location).filter(Boolean))]
  }, [candidates])

  const allAvailabilities = useMemo(() => {
    return ['All', ...new Set(candidates.map((c) => c.availability).filter(Boolean))]
  }, [candidates])

  // Filtered candidate list based on active filters and search query
  const filteredCandidates = useMemo(() => {
    return candidates.filter((c) => {
      const matchesJob = selectedJob === 'all-jobs' || c.jobId === selectedJob
      const matchesSkill = selectedSkill === 'All' || c.skills?.includes(selectedSkill)
      const matchesLocation = selectedLocation === 'All' || c.location === selectedLocation
      const matchesAvailability =
        selectedAvailability === 'All' || c.availability === selectedAvailability

      let matchesExp = true
      const expYears = Number.parseInt(c.experience, 10) || 0
      if (selectedExperience === '5+ years') matchesExp = expYears >= 5
      if (selectedExperience === '3-5 years') matchesExp = expYears >= 3 && expYears < 5
      if (selectedExperience === '<3 years') matchesExp = expYears < 3

      let matchesScore = true
      if (selectedMinScore === '90+') matchesScore = c.score >= 90
      if (selectedMinScore === '80+') matchesScore = c.score >= 80
      if (selectedMinScore === '70+') matchesScore = c.score >= 70

      let matchesSearch = true
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim()
        const nameMatch = c.name?.toLowerCase().includes(q)
        const currentRoleMatch = c.currentRole?.toLowerCase().includes(q)
        const targetRoleMatch = c.targetRole?.toLowerCase().includes(q)
        const skillMatch = c.skills?.some((s) => s.toLowerCase().includes(q))
        matchesSearch = nameMatch || currentRoleMatch || targetRoleMatch || skillMatch
      }

      return (
        matchesJob &&
        matchesSkill &&
        matchesExp &&
        matchesLocation &&
        matchesScore &&
        matchesAvailability &&
        matchesSearch
      )
    })
  }, [
    candidates,
    selectedJob,
    selectedSkill,
    selectedExperience,
    selectedLocation,
    selectedMinScore,
    selectedAvailability,
    searchQuery,
  ])

  // Active candidate: preferred selected candidate or fallback to first filtered candidate
  const activeCandidate = useMemo(() => {
    if (filteredCandidates.length === 0) return null
    const found = filteredCandidates.find((c) => c.id === selectedCandidateId)
    return found || filteredCandidates[0]
  }, [filteredCandidates, selectedCandidateId])

  const activeFilterCount = useMemo(() => {
    let count = 0
    if (selectedJob !== 'all-jobs') count++
    if (selectedSkill !== 'All') count++
    if (selectedExperience !== 'All') count++
    if (selectedLocation !== 'All') count++
    if (selectedMinScore !== 'All') count++
    if (selectedAvailability !== 'All') count++
    if (searchQuery.trim()) count++
    return count
  }, [
    selectedJob,
    selectedSkill,
    selectedExperience,
    selectedLocation,
    selectedMinScore,
    selectedAvailability,
    searchQuery,
  ])

  const handleResetFilters = () => {
    setSelectedJob('all-jobs')
    setSelectedSkill('All')
    setSelectedExperience('All')
    setSelectedLocation('All')
    setSelectedMinScore('All')
    setSelectedAvailability('All')
    setSearchQuery('')
  }

  const handleShortlistCandidate = (candidate) => {
    if (!candidate || shortlistedIds.has(candidate.id)) return

    setShortlistedIds((prev) => new Set([...prev, candidate.id]))
    setToast({
      variant: 'success',
      title: 'Candidate Shortlisted',
      message: `${candidate.name} has been added to your hiring shortlist.`,
    })
  }

  return (
    <div className="space-y-6">
      {/* Toast Feedback */}
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
      <header className="flex flex-col gap-4 border-b border-slate-200 pb-6 dark:border-slate-800 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-brand-700 dark:bg-brand-950/50 dark:text-brand-300">
            <Sparkles className="h-3.5 w-3.5" />
            <span>AI Talent Intelligence</span>
          </div>
          <h1 className="mt-2 text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            AI Candidate Matching
          </h1>
          <p className="mt-1.5 max-w-2xl text-sm leading-relaxed text-slate-600 dark:text-slate-400">
            Intelligent semantic matching evaluating candidate proficiency, verified capabilities, experience depth, and organizational fit.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            onClick={() => navigate('/hiring/shortlist')}
            className="inline-flex items-center gap-2 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          >
            <span>View Shortlist</span>
            {shortlistedIds.size > 0 && (
              <span className="rounded-full bg-brand-600 px-1.5 py-0.2 text-[10px] font-bold text-white">
                {shortlistedIds.size}
              </span>
            )}
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* Error Alert Banner */}
      {error && (
        <div
          role="alert"
          className="flex items-center justify-between rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-200"
        >
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-rose-600 shrink-0 dark:text-rose-400" />
            <div>
              <p className="font-semibold">Unable to load candidate matching data</p>
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

      {/* Search & Multi-Filter Card */}
      <section
        aria-label="Filter candidates"
        className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4 space-y-3 dark:border-slate-800 dark:bg-slate-900/60"
      >
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200/60 pb-3 dark:border-slate-800">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
            <Filter className="h-3.5 w-3.5 text-brand-600 dark:text-brand-400" />
            <span>Filter Candidates</span>
            {activeFilterCount > 0 && (
              <span className="rounded-full bg-brand-100 px-2 py-0.5 text-[10px] font-bold text-brand-700 dark:bg-brand-900/50 dark:text-brand-300">
                {activeFilterCount} active
              </span>
            )}
          </div>

          {activeFilterCount > 0 && (
            <button
              type="button"
              onClick={handleResetFilters}
              className="inline-flex items-center gap-1 text-xs font-semibold text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200 transition"
            >
              <RotateCcw className="h-3 w-3" />
              <span>Reset all filters</span>
            </button>
          )}
        </div>

        {/* Search input */}
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 dark:text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search candidates by name, role, or specific competency..."
            className="w-full rounded-xl border border-slate-200 bg-white pl-10 pr-9 py-2 text-xs font-medium text-slate-800 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-500 transition"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              aria-label="Clear search query"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Filter Dropdowns Grid */}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          {/* Target Role */}
          <div>
            <label
              htmlFor="filter-job"
              className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1"
            >
              Job Role
            </label>
            <select
              id="filter-job"
              value={selectedJob}
              onChange={(e) => setSelectedJob(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 transition"
            >
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title}
                </option>
              ))}
            </select>
          </div>

          {/* Skill */}
          <div>
            <label
              htmlFor="filter-skill"
              className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1"
            >
              Competency
            </label>
            <select
              id="filter-skill"
              value={selectedSkill}
              onChange={(e) => setSelectedSkill(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 transition"
            >
              {allSkills.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          {/* Experience */}
          <div>
            <label
              htmlFor="filter-experience"
              className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1"
            >
              Experience
            </label>
            <select
              id="filter-experience"
              value={selectedExperience}
              onChange={(e) => setSelectedExperience(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 transition"
            >
              <option value="All">All Experience</option>
              <option value="5+ years">5+ years</option>
              <option value="3-5 years">3 - 5 years</option>
              <option value="<3 years">&lt; 3 years</option>
            </select>
          </div>

          {/* Location */}
          <div>
            <label
              htmlFor="filter-location"
              className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1"
            >
              Location
            </label>
            <select
              id="filter-location"
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 transition"
            >
              {allLocations.map((loc) => (
                <option key={loc} value={loc}>
                  {loc}
                </option>
              ))}
            </select>
          </div>

          {/* Min Score */}
          <div>
            <label
              htmlFor="filter-score"
              className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1"
            >
              Match Score
            </label>
            <select
              id="filter-score"
              value={selectedMinScore}
              onChange={(e) => setSelectedMinScore(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 transition"
            >
              <option value="All">All Scores</option>
              <option value="90+">90%+ Match</option>
              <option value="80+">80%+ Match</option>
              <option value="70+">70%+ Match</option>
            </select>
          </div>

          {/* Availability */}
          <div>
            <label
              htmlFor="filter-availability"
              className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1"
            >
              Availability
            </label>
            <select
              id="filter-availability"
              value={selectedAvailability}
              onChange={(e) => setSelectedAvailability(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 transition"
            >
              {allAvailabilities.map((av) => (
                <option key={av} value={av}>
                  {av}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      {/* Main Candidate Match Grid & Details */}
      {loading ? (
        <div className="grid gap-6 lg:grid-cols-[1.3fr_0.9fr]">
          <div className="space-y-3">
            <LoadingSkeleton variant="card" />
            <LoadingSkeleton variant="card" />
            <LoadingSkeleton variant="card" />
          </div>
          <LoadingSkeleton variant="card" className="h-[420px]" />
        </div>
      ) : candidates.length === 0 ? (
        <EmptyState
          title="No candidates registered"
          description="There are currently no candidates in the talent database. Post a job requisition to begin sourcing."
          actionLabel="Post a Job"
          onAction={() => navigate('/hiring/post-job')}
        />
      ) : filteredCandidates.length === 0 ? (
        <EmptyState
          title="No candidates match current criteria"
          description="Try broadening your skill, experience, or match score filters, or clear your search term."
          actionLabel="Reset Filters"
          onAction={handleResetFilters}
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.3fr_0.9fr]">
          {/* Candidates List Column */}
          <section aria-label="Candidate matches" className="space-y-3">
            <div className="flex items-center justify-between px-1 text-xs text-slate-500 dark:text-slate-400">
              <span>
                Showing <strong className="text-slate-900 dark:text-slate-100">{filteredCandidates.length}</strong> matching candidates
              </span>
              <span>Sorted by match score</span>
            </div>

            {filteredCandidates.map((candidate) => {
              const isSelected = activeCandidate?.id === candidate.id
              const isShortlisted = shortlistedIds.has(candidate.id)

              return (
                <button
                  key={candidate.id}
                  type="button"
                  onClick={() => setSelectedCandidateId(candidate.id)}
                  className={`w-full text-left rounded-2xl border p-4 transition-all focus:outline-none focus:ring-2 focus:ring-brand-500/30 ${
                    isSelected
                      ? 'border-brand-500 bg-brand-50/40 ring-2 ring-brand-400/20 shadow-sm dark:border-brand-500 dark:bg-brand-950/30 dark:ring-brand-500/20'
                      : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/60 dark:border-slate-800 dark:bg-slate-900/60 dark:hover:border-slate-700 dark:hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 truncate">
                          {candidate.name}
                        </h2>
                        {candidate.priority && <PriorityTag priority={candidate.priority} />}
                        {isShortlisted && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                            <UserCheck className="h-3 w-3" />
                            <span>Shortlisted</span>
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 truncate">
                        {candidate.currentRole} • {candidate.experience}
                      </p>
                    </div>

                    <MatchScoreBadge score={candidate.score} />
                  </div>

                  {/* Skills preview with SkillChip */}
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {candidate.skills?.slice(0, 4).map((skill) => (
                      <SkillChip
                        key={skill}
                        skill={skill}
                        variant={isSelected ? 'active' : 'default'}
                      />
                    ))}
                    {candidate.skills && candidate.skills.length > 4 && (
                      <span className="self-center text-[10px] font-semibold text-slate-400">
                        +{candidate.skills.length - 4} more
                      </span>
                    )}
                  </div>

                  <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3 w-3 text-slate-400" />
                      {candidate.location}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3 text-slate-400" />
                      Available: {candidate.availability}
                    </span>
                  </div>
                </button>
              )
            })}
          </section>

          {/* Selected Candidate Detailed Evaluation Panel */}
          {activeCandidate && (
            <aside aria-label="Candidate profile evaluation">
              <Card className="p-6 sticky top-24 h-fit border border-slate-200 dark:border-slate-800 dark:bg-slate-900">
                <div className="flex items-start justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
                  <div className="min-w-0 flex-1 pr-2">
                    <div className="flex items-center gap-2">
                      <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100 truncate">
                        {activeCandidate.name}
                      </h3>
                      {shortlistedIds.has(activeCandidate.id) && (
                        <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                          Shortlisted
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                      {activeCandidate.currentRole} → <span className="font-semibold text-slate-700 dark:text-slate-300">{activeCandidate.targetRole}</span>
                    </p>
                  </div>
                  <MatchScoreBadge score={activeCandidate.score} />
                </div>

                <div className="mt-4 space-y-4">
                  {/* Candidate Summary */}
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
                      Candidate Profile Summary
                    </h4>
                    <p className="text-xs leading-relaxed text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-800/60 rounded-xl p-3 border border-slate-100 dark:border-slate-800">
                      {activeCandidate.summary}
                    </p>
                  </div>

                  {/* Metadata Stats */}
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="rounded-xl border border-slate-100 bg-slate-50 p-2.5 dark:border-slate-800 dark:bg-slate-800/60">
                      <p className="text-slate-400 font-medium">Experience</p>
                      <p className="font-bold text-slate-800 dark:text-slate-200 mt-0.5">{activeCandidate.experience}</p>
                    </div>
                    <div className="rounded-xl border border-slate-100 bg-slate-50 p-2.5 dark:border-slate-800 dark:bg-slate-800/60">
                      <p className="text-slate-400 font-medium">Education</p>
                      <p className="font-bold text-slate-800 dark:text-slate-200 mt-0.5">{activeCandidate.education}</p>
                    </div>
                    <div className="rounded-xl border border-slate-100 bg-slate-50 p-2.5 dark:border-slate-800 dark:bg-slate-800/60">
                      <p className="text-slate-400 font-medium">Location</p>
                      <p className="font-bold text-slate-800 dark:text-slate-200 mt-0.5">{activeCandidate.location}</p>
                    </div>
                    <div className="rounded-xl border border-slate-100 bg-slate-50 p-2.5 dark:border-slate-800 dark:bg-slate-800/60">
                      <p className="text-slate-400 font-medium">Availability</p>
                      <p className="font-bold text-slate-800 dark:text-slate-200 mt-0.5">{activeCandidate.availability}</p>
                    </div>
                  </div>

                  {/* Verified Competencies */}
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
                      Verified Competencies
                    </h4>
                    <div className="flex flex-wrap gap-1.5">
                      {activeCandidate.skills?.map((skill) => (
                        <SkillChip key={skill} skill={skill} variant="active" />
                      ))}
                    </div>
                  </div>

                  {/* Match Rationale */}
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
                      Match Rationale & Evidence
                    </h4>
                    <ul className="space-y-1.5 text-xs text-slate-600 dark:text-slate-300">
                      {activeCandidate.reasons?.map((r, i) => (
                        <li key={i} className="flex items-center gap-2">
                          <CheckCircle className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Recruiter Actions */}
                  <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center gap-3">
                    <Button
                      onClick={() => handleShortlistCandidate(activeCandidate)}
                      disabled={shortlistedIds.has(activeCandidate.id)}
                      className="flex-1 inline-flex items-center justify-center gap-2"
                    >
                      {shortlistedIds.has(activeCandidate.id) ? (
                        <>
                          <CheckCircle className="h-4 w-4" />
                          <span>Shortlisted</span>
                        </>
                      ) : (
                        <>
                          <UserPlus className="h-4 w-4" />
                          <span>Shortlist Candidate</span>
                        </>
                      )}
                    </Button>

                    <Button
                      variant="secondary"
                      onClick={() => navigate('/hiring/shortlist')}
                      className="dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                    >
                      Shortlist
                    </Button>
                  </div>
                </div>
              </Card>
            </aside>
          )}
        </div>
      )}
    </div>
  )
}

export default CandidateMatchingPage
