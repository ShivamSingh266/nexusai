import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Users, Filter, MapPin, Clock, Award, CheckCircle, ChevronRight } from 'lucide-react'
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

  // Filters
  const [selectedJob, setSelectedJob] = useState('all-jobs')
  const [selectedSkill, setSelectedSkill] = useState('All')
  const [selectedExperience, setSelectedExperience] = useState('All')
  const [selectedLocation, setSelectedLocation] = useState('All')
  const [selectedMinScore, setSelectedMinScore] = useState('All')
  const [selectedAvailability, setSelectedAvailability] = useState('All')

  const [selectedCandidate, setSelectedCandidate] = useState(null)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    async function loadData() {
      try {
        const [jobsData, candidatesData] = await Promise.all([
          hiringService.getJobOptions(),
          hiringService.getCandidates(),
        ])
        setJobs(jobsData)
        setCandidates(candidatesData)
        if (candidatesData.length > 0) {
          setSelectedCandidate(candidatesData[0])
        }
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  // Collect unique filter options
  const allSkills = useMemo(() => {
    return ['All', ...new Set(candidates.flatMap((c) => c.skills))]
  }, [candidates])

  const allLocations = useMemo(() => {
    return ['All', ...new Set(candidates.map((c) => c.location))]
  }, [candidates])

  const allAvailabilities = useMemo(() => {
    return ['All', ...new Set(candidates.map((c) => c.availability))]
  }, [candidates])

  const filteredCandidates = useMemo(() => {
    return candidates.filter((c) => {
      const matchesJob = selectedJob === 'all-jobs' || c.jobId === selectedJob
      const matchesSkill = selectedSkill === 'All' || c.skills.includes(selectedSkill)
      const matchesLocation = selectedLocation === 'All' || c.location === selectedLocation
      const matchesAvailability = selectedAvailability === 'All' || c.availability === selectedAvailability

      let matchesExp = true
      const expYears = Number.parseInt(c.experience, 10) || 0
      if (selectedExperience === '5+ years') matchesExp = expYears >= 5
      if (selectedExperience === '3-5 years') matchesExp = expYears >= 3 && expYears < 5
      if (selectedExperience === '<3 years') matchesExp = expYears < 3

      let matchesScore = true
      if (selectedMinScore === '90+') matchesScore = c.score >= 90
      if (selectedMinScore === '80+') matchesScore = c.score >= 80
      if (selectedMinScore === '70+') matchesScore = c.score >= 70

      return matchesJob && matchesSkill && matchesExp && matchesLocation && matchesScore && matchesAvailability
    })
  }, [
    candidates,
    selectedJob,
    selectedSkill,
    selectedExperience,
    selectedLocation,
    selectedMinScore,
    selectedAvailability,
  ])

  const handleResetFilters = () => {
    setSelectedJob('all-jobs')
    setSelectedSkill('All')
    setSelectedExperience('All')
    setSelectedLocation('All')
    setSelectedMinScore('All')
    setSelectedAvailability('All')
  }

  const handleShortlistCandidate = (candidate) => {
    setToast({
      variant: 'success',
      title: 'Candidate Shortlisted',
      message: `${candidate.name} has been added to your hiring shortlist.`,
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
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Hiring</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">AI Candidate Matching</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
            Intelligent semantic matching evaluating candidate proficiency, verified capabilities, experience depth, and organizational fit.
          </p>
        </div>

        <Button
          variant="secondary"
          onClick={() => navigate('/hiring/shortlist')}
          className="inline-flex items-center gap-2"
        >
          <span>View Shortlist</span>
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Multi-Filter Bar */}
      <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4 space-y-3">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
          <Filter className="h-3.5 w-3.5 text-brand-600" />
          <span>Filter Candidates</span>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          {/* Target Role */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 mb-1">Job Role</label>
            <select
              value={selectedJob}
              onChange={(e) => setSelectedJob(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-400"
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
            <label className="block text-[11px] font-semibold text-slate-500 mb-1">Skill</label>
            <select
              value={selectedSkill}
              onChange={(e) => setSelectedSkill(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-400"
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
            <label className="block text-[11px] font-semibold text-slate-500 mb-1">Experience</label>
            <select
              value={selectedExperience}
              onChange={(e) => setSelectedExperience(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-400"
            >
              <option value="All">All Experience</option>
              <option value="5+ years">5+ years</option>
              <option value="3-5 years">3 - 5 years</option>
              <option value="<3 years">&lt; 3 years</option>
            </select>
          </div>

          {/* Location */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 mb-1">Location</label>
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-400"
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
            <label className="block text-[11px] font-semibold text-slate-500 mb-1">Match Score</label>
            <select
              value={selectedMinScore}
              onChange={(e) => setSelectedMinScore(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-400"
            >
              <option value="All">All Scores</option>
              <option value="90+">90%+ Match</option>
              <option value="80+">80%+ Match</option>
              <option value="70+">70%+ Match</option>
            </select>
          </div>

          {/* Availability */}
          <div className="flex items-end gap-2">
            <div className="flex-1">
              <label className="block text-[11px] font-semibold text-slate-500 mb-1">Availability</label>
              <select
                value={selectedAvailability}
                onChange={(e) => setSelectedAvailability(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-400"
              >
                {allAvailabilities.map((av) => (
                  <option key={av} value={av}>
                    {av}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="button"
              onClick={handleResetFilters}
              className="rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 transition"
              title="Reset all filters"
            >
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* Main Candidate Match Grid & Details */}
      {loading ? (
        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <LoadingSkeleton variant="card" />
          <LoadingSkeleton variant="card" />
        </div>
      ) : filteredCandidates.length === 0 ? (
        <EmptyState
          title="No candidates match current criteria"
          description="Try broadening your skill, experience, or match score filters."
          actionLabel="Reset Filters"
          onAction={handleResetFilters}
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.3fr_0.9fr]">
          {/* Candidates List */}
          <div className="space-y-3">
            {filteredCandidates.map((candidate) => {
              const isSelected = selectedCandidate?.id === candidate.id

              return (
                <div
                  key={candidate.id}
                  onClick={() => setSelectedCandidate(candidate)}
                  className={`cursor-pointer rounded-2xl border p-4 transition-all ${
                    isSelected
                      ? 'border-brand-500 bg-brand-50/30 ring-2 ring-brand-400/20 shadow-sm'
                      : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-bold text-slate-900">{candidate.name}</h3>
                        <PriorityTag priority={candidate.priority} />
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {candidate.currentRole} • {candidate.experience}
                      </p>
                    </div>

                    <MatchScoreBadge score={candidate.score} />
                  </div>

                  {/* Skills preview with SkillChip */}
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {candidate.skills.map((skill) => (
                      <SkillChip
                        key={skill}
                        skill={skill}
                        variant={isSelected ? 'active' : 'default'}
                      />
                    ))}
                  </div>

                  <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3 w-3 text-slate-400" />
                      {candidate.location}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3 text-slate-400" />
                      Available: {candidate.availability}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Selected Candidate Detailed Evaluation Panel */}
          {selectedCandidate && (
            <Card className="p-6 sticky top-24 h-fit">
              <div className="flex items-start justify-between border-b border-slate-100 pb-4">
                <div>
                  <h3 className="text-xl font-bold text-slate-900">{selectedCandidate.name}</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {selectedCandidate.currentRole} → {selectedCandidate.targetRole}
                  </p>
                </div>
                <MatchScoreBadge score={selectedCandidate.score} />
              </div>

              <div className="mt-4 space-y-4">
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1.5">
                    Candidate Profile Summary
                  </h4>
                  <p className="text-xs leading-relaxed text-slate-600 bg-slate-50 rounded-xl p-3 border border-slate-100">
                    {selectedCandidate.summary}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="rounded-xl border border-slate-100 bg-slate-50 p-2.5">
                    <p className="text-slate-400 font-medium">Experience</p>
                    <p className="font-bold text-slate-800 mt-0.5">{selectedCandidate.experience}</p>
                  </div>
                  <div className="rounded-xl border border-slate-100 bg-slate-50 p-2.5">
                    <p className="text-slate-400 font-medium">Education</p>
                    <p className="font-bold text-slate-800 mt-0.5">{selectedCandidate.education}</p>
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                    Verified Competencies
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedCandidate.skills.map((skill) => (
                      <SkillChip key={skill} skill={skill} variant="active" />
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                    Match Rationale
                  </h4>
                  <ul className="space-y-1.5 text-xs text-slate-600">
                    {selectedCandidate.reasons.map((r, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <CheckCircle className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="pt-4 border-t border-slate-100 flex items-center gap-3">
                  <Button
                    onClick={() => handleShortlistCandidate(selectedCandidate)}
                    className="flex-1"
                  >
                    Shortlist Candidate
                  </Button>

                  <Button
                    variant="secondary"
                    onClick={() => navigate('/hiring/shortlist')}
                  >
                    Shortlist
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}

export default CandidateMatchingPage
