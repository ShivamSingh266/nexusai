import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppShell } from '../../components/layout/AppShell'
import { PageContainer } from '../../components/layout/PageContainer'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { candidateMatchData, jobOptions } from '../../mocks/candidateMatchingMockData'

const formatStatusClass = (status) => {
  const map = {
    'Strong Match': 'bg-emerald-100 text-emerald-700',
    'Good Match': 'bg-blue-100 text-blue-700',
    'Potential Match': 'bg-amber-100 text-amber-700',
  }

  return map[status] || 'bg-slate-100 text-slate-700'
}

const scoreLabel = (score) => {
  if (score >= 90) return 'Strong Match'
  if (score >= 80) return 'Good Match'
  return 'Potential Match'
}

export function CandidateMatchingPage() {
  const navigate = useNavigate()
  const [selectedJobId, setSelectedJobId] = useState(jobOptions[0].id)
  const [selectedCandidateId, setSelectedCandidateId] = useState(candidateMatchData[0].id)
  const [matchFilter, setMatchFilter] = useState('All')
  const [experienceFilter, setExperienceFilter] = useState('All')
  const [skillFilter, setSkillFilter] = useState('All')
  const [statusFilter, setStatusFilter] = useState('All')

  const selectedJob = jobOptions.find((job) => job.id === selectedJobId) || jobOptions[0]
  const filteredCandidates = useMemo(() => {
    const selectedJobCandidates = candidateMatchData.filter((candidate) => candidate.jobId === selectedJobId)

    return selectedJobCandidates.filter((candidate) => {
      const matchesScore = matchFilter === 'All' || scoreLabel(candidate.score) === matchFilter
      const matchesExperience =
        experienceFilter === 'All' ||
        (experienceFilter === '5+ years' && Number.parseInt(candidate.experience, 10) >= 5) ||
        (experienceFilter === '3+ years' && Number.parseInt(candidate.experience, 10) >= 3)
      const matchesSkill = skillFilter === 'All' || candidate.skills.includes(skillFilter)
      const matchesStatus = statusFilter === 'All' || candidate.status === statusFilter

      return matchesScore && matchesExperience && matchesSkill && matchesStatus
    })
  }, [selectedJobId, matchFilter, experienceFilter, skillFilter, statusFilter])

  const selectedCandidate =
    filteredCandidates.find((candidate) => candidate.id === selectedCandidateId) ||
    filteredCandidates[0] ||
    candidateMatchData.find((candidate) => candidate.jobId === selectedJobId) ||
    candidateMatchData[0]

  const summary = useMemo(() => {
    const items = candidateMatchData.filter((candidate) => candidate.jobId === selectedJobId)
    const strongMatches = items.filter((candidate) => candidate.score >= 90).length
    const shortlisted = items.filter((candidate) => candidate.status !== 'Potential Match').length
    const averageScore = items.length
      ? Math.round(items.reduce((sum, candidate) => sum + candidate.score, 0) / items.length)
      : 0

    return {
      analyzed: items.length,
      strongMatches,
      shortlisted,
      averageScore,
    }
  }, [selectedJobId])

  const uniqueSkills = Array.from(
    new Set(candidateMatchData.filter((candidate) => candidate.jobId === selectedJobId).flatMap((candidate) => candidate.skills)),
  )

  const handleCandidateAction = (action, candidateId) => {
    setSelectedCandidateId(candidateId)

    if (action === 'Shortlist') {
      navigate('/hiring/shortlist')
      return
    }

    window.alert(`${action} action triggered for frontend-only review. No backend call was made.`)
  }

  return (
    <AppShell title="Hiring Dashboard">
      <PageContainer>
        <div className="flex flex-col gap-3 border-b border-slate-200 pb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Hiring</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Candidate Matching</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              NexusAI helps identify suitable candidates for a role by comparing skills, experience, and fit signals.
            </p>
          </div>
        </div>

        <Card className="p-5">
          <div className="grid gap-5 md:grid-cols-[1.2fr_2fr] md:items-end">
            <label className="block text-sm font-medium text-slate-700">
              Select Job
              <select
                value={selectedJobId}
                onChange={(event) => {
                  setSelectedJobId(event.target.value)
                  const nextCandidate = candidateMatchData.find(
                    (candidate) => candidate.jobId === event.target.value,
                  )
                  if (nextCandidate) setSelectedCandidateId(nextCandidate.id)
                }}
                className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
              >
                {jobOptions.map((job) => (
                  <option key={job.id} value={job.id}>
                    {job.title}
                  </option>
                ))}
              </select>
            </label>

            <div className="rounded-xl border border-brand-100 bg-brand-50 px-4 py-3">
              <div className="text-xs uppercase tracking-[0.18em] text-brand-700">Selected Role</div>
              <div className="mt-1 text-lg font-semibold text-slate-900">{selectedJob.title}</div>
              <div className="text-sm text-slate-600">
                {selectedJob.department} • {selectedJob.location}
              </div>
            </div>
          </div>
        </Card>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Card className="p-5">
            <p className="text-sm text-slate-500">Candidates Analyzed</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">{summary.analyzed}</p>
          </Card>
          <Card className="p-5">
            <p className="text-sm text-slate-500">Strong Matches</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">{summary.strongMatches}</p>
          </Card>
          <Card className="p-5">
            <p className="text-sm text-slate-500">Shortlisted</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">{summary.shortlisted}</p>
          </Card>
          <Card className="p-5">
            <p className="text-sm text-slate-500">Average Match Score</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">{summary.averageScore}%</p>
          </Card>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.5fr_0.8fr]">
          <Card className="p-5">
            <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Matching Results</h2>
              <div className="flex flex-wrap gap-2">
                <select
                  value={matchFilter}
                  onChange={(event) => setMatchFilter(event.target.value)}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
                >
                  <option value="All">All Match Scores</option>
                  <option value="Strong Match">Strong Match</option>
                  <option value="Good Match">Good Match</option>
                  <option value="Potential Match">Potential Match</option>
                </select>

                <select
                  value={experienceFilter}
                  onChange={(event) => setExperienceFilter(event.target.value)}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
                >
                  <option value="All">All Experience</option>
                  <option value="5+ years">5+ years</option>
                  <option value="3+ years">3+ years</option>
                </select>

                <select
                  value={skillFilter}
                  onChange={(event) => setSkillFilter(event.target.value)}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
                >
                  <option value="All">All Skills</option>
                  {uniqueSkills.map((skill) => (
                    <option key={skill} value={skill}>
                      {skill}
                    </option>
                  ))}
                </select>

                <select
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value)}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
                >
                  <option value="All">All Status</option>
                  <option value="Strong Match">Strong Match</option>
                  <option value="Good Match">Good Match</option>
                  <option value="Potential Match">Potential Match</option>
                </select>
              </div>
            </div>

            <div className="space-y-3">
              {filteredCandidates.length > 0 ? (
                filteredCandidates.map((candidate) => (
                  <button
                    key={candidate.id}
                    type="button"
                    onClick={() => setSelectedCandidateId(candidate.id)}
                    className={`w-full rounded-xl border p-4 text-left transition ${
                      selectedCandidate?.id === candidate.id
                        ? 'border-brand-200 bg-brand-50'
                        : 'border-slate-200 bg-slate-50 hover:border-brand-200 hover:bg-white'
                    }`}
                  >
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                      <div>
                        <div className="flex items-center gap-3">
                          <div className="font-semibold text-slate-900">{candidate.name}</div>
                          <span className={`rounded-full px-2 py-1 text-[10px] font-semibold ${formatStatusClass(candidate.status)}`}>
                            {candidate.status}
                          </span>
                        </div>
                        <div className="mt-1 text-sm text-slate-500">
                          {candidate.currentRole} • {candidate.experience}
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <div className="text-xs text-slate-500">Match Score</div>
                          <div className="text-xl font-bold text-slate-900">{candidate.score}%</div>
                        </div>
                        <div className="w-24">
                          <div className="h-2 rounded-full bg-slate-200">
                            <div
                              className="h-2 rounded-full bg-brand-600"
                              style={{ width: `${candidate.score}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="mt-3 flex flex-wrap gap-2">
                      {candidate.skills.map((skill) => (
                        <span key={skill} className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-slate-600 ring-1 ring-slate-200">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </button>
                ))
              ) : (
                <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">
                  No candidates match the current filters.
                </div>
              )}
            </div>
          </Card>

          <Card className="p-5">
            {selectedCandidate ? (
              <>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-xs uppercase tracking-[0.18em] text-brand-700">Candidate Overview</div>
                    <h2 className="mt-2 text-xl font-semibold text-slate-900">{selectedCandidate.name}</h2>
                  </div>
                  <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${formatStatusClass(selectedCandidate.status)}`}>
                    {selectedCandidate.status}
                  </span>
                </div>

                <div className="mt-5 space-y-4">
                  <div>
                    <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Role</div>
                    <div className="mt-1 text-sm font-medium text-slate-700">{selectedCandidate.targetRole}</div>
                  </div>

                  <div>
                    <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Current Role</div>
                    <div className="mt-1 text-sm font-medium text-slate-700">{selectedCandidate.currentRole}</div>
                  </div>

                  <div>
                    <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Experience</div>
                    <div className="mt-1 text-sm font-medium text-slate-700">{selectedCandidate.experience}</div>
                  </div>

                  <div>
                    <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Education</div>
                    <div className="mt-1 text-sm font-medium text-slate-700">{selectedCandidate.education}</div>
                  </div>

                  <div>
                    <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Availability</div>
                    <div className="mt-1 text-sm font-medium text-slate-700">{selectedCandidate.availability}</div>
                  </div>

                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-sm font-medium text-slate-700">Match Score</span>
                      <span className="text-sm font-semibold text-slate-900">{selectedCandidate.score}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-slate-200">
                      <div
                        className="h-2 rounded-full bg-brand-600"
                        style={{ width: `${selectedCandidate.score}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Why this match</div>
                    <ul className="mt-2 space-y-2 text-sm text-slate-600">
                      {selectedCandidate.reasons.map((reason) => (
                        <li key={reason} className="flex items-start gap-2">
                          <span className="mt-1 inline-block h-2 w-2 rounded-full bg-brand-500" />
                          <span>{reason}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="flex flex-wrap gap-2 pt-2">
                    <Button type="button" onClick={() => handleCandidateAction('Review', selectedCandidate.id)}>
                      Review
                    </Button>
                    <Button type="button" variant="secondary" onClick={() => handleCandidateAction('Shortlist', selectedCandidate.id)}>
                      Shortlist
                    </Button>
                    <Button type="button" variant="ghost" onClick={() => handleCandidateAction('Reject', selectedCandidate.id)}>
                      Reject
                    </Button>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-sm text-slate-500">Select a candidate to review.</div>
            )}
          </Card>
        </section>
      </PageContainer>
    </AppShell>
  )
}
