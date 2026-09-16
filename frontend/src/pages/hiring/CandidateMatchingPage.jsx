import { useEffect, useMemo, useState } from 'react'
import { AppShell } from '../../components/layout/AppShell'
import { PageContainer } from '../../components/layout/PageContainer'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { ApiError } from '../../services/api'
import { useAuth } from '../../auth/AuthContext'
import { createShortlist, getCandidateMatches, listJobs } from '../../services/recruiter'

const scoreLabel = (score) => {
  if (score >= 0.9) return 'Strong Match'
  if (score >= 0.8) return 'Good Match'
  return 'Potential Match'
}

const scoreClass = (label) => ({
  'Strong Match': 'bg-emerald-100 text-emerald-700',
  'Good Match': 'bg-blue-100 text-blue-700',
  'Potential Match': 'bg-amber-100 text-amber-700',
}[label] || 'bg-slate-100 text-slate-700')

const scorePercent = (score) => Math.round(score * 100)

const componentLabel = {
  skill_coverage: 'Skill coverage',
  experience: 'Experience',
  education: 'Education',
  location_work_mode: 'Location / work mode',
}

export function CandidateMatchingPage() {
  const { accessToken } = useAuth()
  const [jobs, setJobs] = useState([])
  const [selectedJobId, setSelectedJobId] = useState('')
  const [matches, setMatches] = useState([])
  const [selectedCandidateId, setSelectedCandidateId] = useState(null)
  const [jobsLoading, setJobsLoading] = useState(true)
  const [matchesLoading, setMatchesLoading] = useState(true)
  const [error, setError] = useState('')
  const [shortlistMessage, setShortlistMessage] = useState('')
  const [shortlistingId, setShortlistingId] = useState(null)

  useEffect(() => {
    let active = true
    listJobs(accessToken)
      .then((response) => {
        if (active) {
          setJobs(response.data)
          const firstJobId = String(response.data[0]?.id || '')
          setSelectedJobId((current) => current || firstJobId)
          setMatchesLoading(Boolean(firstJobId))
        }
      })
      .catch((requestError) => { if (active) setError(requestError.message) })
      .finally(() => { if (active) setJobsLoading(false) })
    return () => { active = false }
  }, [accessToken])

  useEffect(() => {
    if (!selectedJobId) {
      return undefined
    }
    let active = true
    getCandidateMatches(selectedJobId, accessToken)
      .then((response) => {
        if (active) {
          setMatches(response.data)
          setSelectedCandidateId(response.data[0]?.candidate_id || null)
        }
      })
      .catch((requestError) => {
        if (active) {
          setMatches([])
          setSelectedCandidateId(null)
          if (requestError instanceof ApiError && requestError.status === 422) {
            setError('This job has no usable canonical skills. Attach canonical skills before running matching.')
          } else {
            setError(requestError.message)
          }
        }
      })
      .finally(() => { if (active) setMatchesLoading(false) })
    return () => { active = false }
  }, [accessToken, selectedJobId])

  const selectedJob = jobs.find((job) => String(job.id) === selectedJobId)
  const selectedCandidate = matches.find((candidate) => candidate.candidate_id === selectedCandidateId) || matches[0]
  const summary = useMemo(() => ({
    analyzed: matches.length,
    strongMatches: matches.filter((candidate) => candidate.score >= 0.9).length,
    averageScore: matches.length
      ? Math.round(matches.reduce((sum, candidate) => sum + candidate.score, 0) / matches.length * 100)
      : 0,
  }), [matches])

  const shortlistCandidate = async (candidate) => {
    if (!selectedJob || shortlistingId) return
    setShortlistingId(candidate.candidate_id)
    setError('')
    setShortlistMessage('')
    try {
      await createShortlist({
        job_id: selectedJob.id,
        candidate_id: candidate.candidate_id,
        match_score: candidate.score,
      }, accessToken)
      setShortlistMessage(`Candidate #${candidate.candidate_id} was added to the shortlist.`)
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 409) {
        setShortlistMessage(`Candidate #${candidate.candidate_id} is already shortlisted for this job.`)
      } else {
        setError(requestError instanceof ApiError && requestError.status === 422
          ? 'This job has no usable canonical skills. Attach canonical skills before shortlisting.'
          : requestError.message)
      }
    } finally {
      setShortlistingId(null)
    }
  }

  const changeJob = (jobId) => {
    setSelectedJobId(jobId)
    setMatches([])
    setSelectedCandidateId(null)
    setMatchesLoading(Boolean(jobId))
    setError('')
    setShortlistMessage('')
  }

  return (
    <AppShell title="Hiring Dashboard">
      <PageContainer>
        <div className="border-b border-slate-200 pb-6">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Hiring</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Candidate Matching</h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-600">Review backend-generated candidate matches for your recruiter-owned jobs.</p>
        </div>

        {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {shortlistMessage ? <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{shortlistMessage}</p> : null}

        <Card className="p-5">
          <label className="block max-w-xl text-sm font-medium text-slate-700">
            Select Job
            <select value={selectedJobId} disabled={jobsLoading} onChange={(event) => changeJob(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm">
              <option value="">{jobsLoading ? 'Loading jobs...' : jobs.length ? 'Select a job' : 'No recruiter jobs found'}</option>
              {jobs.map((job) => <option key={job.id} value={job.id}>{job.title} — {job.location || 'Location not specified'}</option>)}
            </select>
          </label>
        </Card>

        {!jobsLoading && jobs.length === 0 ? <Card className="p-8 text-center text-sm text-slate-500">No recruiter jobs found. Create a job before running candidate matching.</Card> : null}
        {selectedJob ? <div className="rounded-xl border border-brand-100 bg-brand-50 px-4 py-3"><div className="text-xs uppercase tracking-[0.18em] text-brand-700">Selected Role</div><div className="mt-1 text-lg font-semibold text-slate-900">{selectedJob.title}</div><div className="text-sm text-slate-600">{selectedJob.location || 'Location not specified'}</div></div> : null}

        <section className="grid gap-4 md:grid-cols-3">
          <Card className="p-5"><p className="text-sm text-slate-500">Candidates Analyzed</p><p className="mt-3 text-3xl font-bold text-slate-900">{summary.analyzed}</p></Card>
          <Card className="p-5"><p className="text-sm text-slate-500">Strong Matches</p><p className="mt-3 text-3xl font-bold text-slate-900">{summary.strongMatches}</p></Card>
          <Card className="p-5"><p className="text-sm text-slate-500">Average Match Score</p><p className="mt-3 text-3xl font-bold text-slate-900">{summary.averageScore}%</p></Card>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.5fr_0.8fr]">
          <Card className="p-5">
            <h2 className="mb-4 text-lg font-semibold text-slate-900">Matching Results</h2>
            {matchesLoading ? <p className="p-5 text-sm text-slate-600">Loading matches...</p> : matches.length === 0 ? <p className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">{selectedJob ? 'No matches returned for this job.' : 'Select a job to load matches.'}</p> : (
              <div className="space-y-3">
                {matches.map((candidate) => {
                  const label = scoreLabel(candidate.score)
                  return <button type="button" key={candidate.candidate_id} onClick={() => setSelectedCandidateId(candidate.candidate_id)} className={`w-full rounded-xl border p-4 text-left ${candidate.candidate_id === selectedCandidate?.candidate_id ? 'border-brand-300 bg-brand-50' : 'border-slate-200 bg-white'}`}>
                    <div className="flex items-center justify-between gap-3"><div><div className="font-semibold text-slate-900">Candidate #{candidate.candidate_id}</div><span className={`mt-2 inline-flex rounded-full px-2 py-1 text-[10px] font-semibold ${scoreClass(label)}`}>{label}</span></div><div className="text-right"><div className="text-xs text-slate-500">Match Score</div><div className="text-xl font-bold text-slate-900">{scorePercent(candidate.score)}%</div></div></div>
                    <div className="mt-3 h-2 rounded-full bg-slate-200"><div className="h-2 rounded-full bg-brand-600" style={{ width: `${scorePercent(candidate.score)}%` }} /></div>
                  </button>
                })}
              </div>
            )}
          </Card>

          <Card className="p-5">
            {selectedCandidate ? <><div className="flex items-center justify-between gap-3"><div><div className="text-xs uppercase tracking-[0.18em] text-brand-700">Candidate Overview</div><h2 className="mt-2 text-xl font-semibold text-slate-900">Candidate #{selectedCandidate.candidate_id}</h2></div><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${scoreClass(scoreLabel(selectedCandidate.score))}`}>{scoreLabel(selectedCandidate.score)}</span></div>
              <div className="mt-5 space-y-4">
                <div><div className="text-xs uppercase tracking-[0.18em] text-slate-500">Match Score</div><div className="mt-1 text-sm font-medium text-slate-700">{scorePercent(selectedCandidate.score)}%</div></div>
                <div><div className="text-xs uppercase tracking-[0.18em] text-slate-500">Component Scores</div><div className="mt-2 space-y-2 text-sm text-slate-600">{Object.entries(selectedCandidate.component_scores || {}).map(([name, value]) => <div key={name} className="flex justify-between gap-3"><span>{componentLabel[name] || name}</span><span className="font-medium text-slate-900">{scorePercent(value)}%</span></div>)}</div></div>
                <div><div className="text-xs uppercase tracking-[0.18em] text-slate-500">Explanation</div><p className="mt-2 text-sm leading-6 text-slate-700">{selectedCandidate.explanation || 'No explanation provided.'}</p></div>
                <div><div className="text-xs uppercase tracking-[0.18em] text-slate-500">Taxonomy Version</div><p className="mt-1 text-sm text-slate-700">{selectedCandidate.taxonomy_version}</p></div>
                {selectedCandidate.available_components?.length ? <p className="text-xs text-slate-500">Available components: {selectedCandidate.available_components.join(', ')}</p> : null}
                {selectedCandidate.omitted_components?.length ? <p className="text-xs text-slate-500">Omitted components: {selectedCandidate.omitted_components.join(', ')}</p> : null}
                {selectedCandidate.warnings?.length ? <div className="rounded-lg bg-amber-50 p-3 text-xs text-amber-800">Warnings: {selectedCandidate.warnings.join(' ')}</div> : null}
                <Button type="button" variant="secondary" disabled={shortlistingId === selectedCandidate.candidate_id} onClick={() => shortlistCandidate(selectedCandidate)}>{shortlistingId === selectedCandidate.candidate_id ? 'Shortlisting...' : 'Shortlist Candidate'}</Button>
              </div>
            </> : <div className="text-sm text-slate-500">Select a match to review.</div>}
          </Card>
        </section>
      </PageContainer>
    </AppShell>
  )
}
