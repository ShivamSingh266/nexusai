import { useMemo, useState } from 'react'
import { AppShell } from '../../components/layout/AppShell'
import { PageContainer } from '../../components/layout/PageContainer'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { shortlistCandidates } from '../../mocks/shortlistMockData'

const stageStyles = {
  Shortlisted: 'bg-violet-100 text-violet-700',
  Review: 'bg-amber-100 text-amber-700',
  Interview: 'bg-blue-100 text-blue-700',
  Selected: 'bg-emerald-100 text-emerald-700',
  Rejected: 'bg-red-100 text-red-700',
}

const stageOptions = ['All', 'Shortlisted', 'Review', 'Interview', 'Selected', 'Rejected']

export function ShortlistPage() {
  const [roleFilter, setRoleFilter] = useState('All')
  const [stageFilter, setStageFilter] = useState('All')
  const [matchFilter, setMatchFilter] = useState('All')
  const [experienceFilter, setExperienceFilter] = useState('All')
  const [selectedCandidateId, setSelectedCandidateId] = useState(shortlistCandidates[0]?.id || '')

  const candidateRoles = ['All', ...new Set(shortlistCandidates.map((candidate) => candidate.role))]

  const filteredCandidates = useMemo(() => {
    return shortlistCandidates.filter((candidate) => {
      const matchesRole = roleFilter === 'All' || candidate.role === roleFilter
      const matchesStage = stageFilter === 'All' || candidate.stage === stageFilter
      const matchesMatch =
        matchFilter === 'All' ||
        (matchFilter === '90+' && candidate.matchScore >= 90) ||
        (matchFilter === '80+' && candidate.matchScore >= 80) ||
        (matchFilter === '70+' && candidate.matchScore >= 70)
      const matchesExperience =
        experienceFilter === 'All' ||
        (experienceFilter === '5+ years' && Number.parseInt(candidate.experience, 10) >= 5) ||
        (experienceFilter === '3+ years' && Number.parseInt(candidate.experience, 10) >= 3)

      return matchesRole && matchesStage && matchesMatch && matchesExperience
    })
  }, [roleFilter, stageFilter, matchFilter, experienceFilter])

  const selectedCandidate =
    filteredCandidates.find((candidate) => candidate.id === selectedCandidateId) ||
    filteredCandidates[0] ||
    shortlistCandidates[0]

  const summary = useMemo(() => {
    const strongMatches = shortlistCandidates.filter((candidate) => candidate.matchScore >= 90).length
    const interviewsPending = shortlistCandidates.filter((candidate) => candidate.stage === 'Interview').length
    const offersSelected = shortlistCandidates.filter((candidate) => candidate.stage === 'Selected').length

    return {
      total: shortlistCandidates.length,
      strongMatches,
      interviewsPending,
      offersSelected,
    }
  }, [])

  const updateCandidateStage = (candidateId, nextStage) => {
    setSelectedCandidateId(candidateId)
    const candidate = shortlistCandidates.find((item) => item.id === candidateId)
    if (candidate) {
      candidate.stage = nextStage
      window.alert(`Frontend-only stage change: ${candidate.name} moved to ${nextStage}.`)
    }
  }

  const removeCandidate = (candidateId) => {
    const candidate = shortlistCandidates.find((item) => item.id === candidateId)
    if (candidate) {
      window.alert(`${candidate.name} removed from the shortlist in the frontend only.`)
    }
  }

  return (
    <AppShell title="Hiring Dashboard">
      <PageContainer>
        <div className="flex flex-col gap-3 border-b border-slate-200 pb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Hiring</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Shortlisted Candidates</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              Review the talent you have shortlisted and keep the hiring pipeline moving with a clear frontend view.
            </p>
          </div>
        </div>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Card className="p-5">
            <p className="text-sm text-slate-500">Total Shortlisted</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">{summary.total}</p>
          </Card>
          <Card className="p-5">
            <p className="text-sm text-slate-500">Strong Matches</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">{summary.strongMatches}</p>
          </Card>
          <Card className="p-5">
            <p className="text-sm text-slate-500">Interviews Pending</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">{summary.interviewsPending}</p>
          </Card>
          <Card className="p-5">
            <p className="text-sm text-slate-500">Offers / Selected</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">{summary.offersSelected}</p>
          </Card>
        </section>

        <Card className="p-5">
          <div className="mb-4 flex flex-col gap-3 md:flex-row md:flex-wrap md:items-center md:justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Shortlist Filters</h2>
            <div className="flex flex-wrap gap-2">
              <select
                value={roleFilter}
                onChange={(event) => setRoleFilter(event.target.value)}
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
              >
                {candidateRoles.map((role) => (
                  <option key={role} value={role}>
                    {role === 'All' ? 'All Roles' : role}
                  </option>
                ))}
              </select>

              <select
                value={stageFilter}
                onChange={(event) => setStageFilter(event.target.value)}
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
              >
                {stageOptions.map((stage) => (
                  <option key={stage} value={stage}>
                    {stage === 'All' ? 'All Stages' : stage}
                  </option>
                ))}
              </select>

              <select
                value={matchFilter}
                onChange={(event) => setMatchFilter(event.target.value)}
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
              >
                <option value="All">All Match Scores</option>
                <option value="90+">90%+</option>
                <option value="80+">80%+</option>
                <option value="70+">70%+</option>
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
            </div>
          </div>

          {filteredCandidates.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-700">
                <thead className="bg-slate-50 text-slate-600">
                  <tr>
                    <th className="px-4 py-3 font-medium">Candidate</th>
                    <th className="px-4 py-3 font-medium">Applied Role</th>
                    <th className="px-4 py-3 font-medium">Match</th>
                    <th className="px-4 py-3 font-medium">Experience</th>
                    <th className="px-4 py-3 font-medium">Skills</th>
                    <th className="px-4 py-3 font-medium">Stage</th>
                    <th className="px-4 py-3 font-medium">Shortlisted</th>
                    <th className="px-4 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCandidates.map((candidate) => (
                    <tr key={candidate.id} className="border-t border-slate-200">
                      <td className="px-4 py-4">
                        <button
                          type="button"
                          className="text-left font-semibold text-slate-900 hover:text-brand-700"
                          onClick={() => setSelectedCandidateId(candidate.id)}
                        >
                          {candidate.name}
                        </button>
                      </td>
                      <td className="px-4 py-4">{candidate.role}</td>
                      <td className="px-4 py-4 font-semibold text-slate-900">{candidate.matchScore}%</td>
                      <td className="px-4 py-4">{candidate.experience}</td>
                      <td className="px-4 py-4">
                        <div className="flex flex-wrap gap-1">
                          {candidate.skills.slice(0, 2).map((skill) => (
                            <span
                              key={skill}
                              className="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-medium text-slate-600"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${stageStyles[candidate.stage]}`}>
                          {candidate.stage}
                        </span>
                      </td>
                      <td className="px-4 py-4">{candidate.dateShortlisted}</td>
                      <td className="px-4 py-4">
                        <div className="flex flex-wrap gap-2">
                          <Button
                            type="button"
                            variant="secondary"
                            className="px-2.5 py-2 text-[10px]"
                            onClick={() => setSelectedCandidateId(candidate.id)}
                          >
                            Review
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            className="px-2.5 py-2 text-[10px]"
                            onClick={() => updateCandidateStage(candidate.id, 'Interview')}
                          >
                            Interview
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            className="px-2.5 py-2 text-[10px]"
                            onClick={() => updateCandidateStage(candidate.id, 'Selected')}
                          >
                            Select
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">
              No shortlisted candidates match the current filters.
            </div>
          )}
        </Card>

        <Card className="p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Candidate Review</h2>
            <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${stageStyles[selectedCandidate.stage]}`}>
              {selectedCandidate.stage}
            </span>
          </div>

          <div className="grid gap-6 lg:grid-cols-[1.1fr_1.6fr]">
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Selected Candidate</div>
              <div className="mt-3 text-2xl font-bold text-slate-900">{selectedCandidate.name}</div>
              <div className="mt-1 text-sm text-slate-600">{selectedCandidate.role}</div>

              <div className="mt-5 space-y-3 text-sm text-slate-600">
                <div>
                  <span className="text-slate-500">Education:</span> {selectedCandidate.education}
                </div>
                <div>
                  <span className="text-slate-500">Experience:</span> {selectedCandidate.experience}
                </div>
                <div>
                  <span className="text-slate-500">Match Score:</span> {selectedCandidate.matchScore}%
                </div>
                <div>
                  <span className="text-slate-500">Date shortlisted:</span> {selectedCandidate.dateShortlisted}
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Summary</div>
                <p className="mt-2 text-sm leading-6 text-slate-700">{selectedCandidate.summary}</p>
              </div>

              <div>
                <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Skills</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {selectedCandidate.skills.map((skill) => (
                    <span key={skill} className="rounded-full bg-brand-50 px-2.5 py-1 text-xs font-medium text-brand-700">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Why this match</div>
                <p className="mt-2 text-sm leading-6 text-slate-700">{selectedCandidate.reason}</p>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button type="button" onClick={() => updateCandidateStage(selectedCandidate.id, 'Interview')}>
                  Move to Interview
                </Button>
                <Button type="button" variant="secondary" onClick={() => updateCandidateStage(selectedCandidate.id, 'Selected')}>
                  Mark Selected
                </Button>
                <Button type="button" variant="ghost" onClick={() => removeCandidate(selectedCandidate.id)}>
                  Remove from Shortlist
                </Button>
              </div>
            </div>
          </div>
        </Card>
      </PageContainer>
    </AppShell>
  )
}
