import { useEffect, useMemo, useState } from 'react'
import { AppShell } from '../../components/layout/AppShell'
import { PageContainer } from '../../components/layout/PageContainer'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { ApiError } from '../../services/api'
import { useAuth } from '../../auth/AuthContext'
import { deleteShortlist, listJobs, listShortlists, listShortlistsForJob, updateShortlist } from '../../services/recruiter'

const scorePercent = (score) => (score === null || score === undefined ? null : Math.round(score * 100))

export function ShortlistPage() {
  const { accessToken } = useAuth()
  const [jobs, setJobs] = useState([])
  const [selectedJobId, setSelectedJobId] = useState('')
  const [shortlists, setShortlists] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [notes, setNotes] = useState('')
  const [jobsLoading, setJobsLoading] = useState(true)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [savingId, setSavingId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    let active = true
    listJobs(accessToken)
      .then((response) => { if (active) setJobs(response.data) })
      .catch((requestError) => { if (active) setError(requestError.message) })
      .finally(() => { if (active) setJobsLoading(false) })
    return () => { active = false }
  }, [accessToken])

  useEffect(() => {
    let active = true
    const request = selectedJobId
      ? listShortlistsForJob(selectedJobId, accessToken)
      : listShortlists(accessToken)
    request
      .then((records) => {
        if (active) {
          setShortlists(records)
          setSelectedId(records[0]?.id || null)
          setNotes(records[0]?.notes || '')
        }
      })
      .catch((requestError) => { if (active) setError(requestError.message) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [accessToken, selectedJobId])

  const changeJob = (jobId) => {
    setLoading(true)
    setError('')
    setNotice('')
    setSelectedJobId(jobId)
  }

  const selected = shortlists.find((record) => record.id === selectedId) || shortlists[0]
  const selectedJob = jobs.find((job) => job.id === selected?.job_id)
  const summary = useMemo(() => ({
    total: shortlists.length,
    strong: shortlists.filter((record) => (record.match_score || 0) >= 0.9).length,
  }), [shortlists])

  const selectRecord = (record) => {
    setSelectedId(record.id)
    setNotes(record.notes || '')
    setNotice('')
  }

  const saveNotes = async () => {
    if (!selected || savingId) return
    setSavingId(selected.id)
    setError('')
    setNotice('')
    try {
      const updated = await updateShortlist(selected.id, { notes: notes.slice(0, 2000) }, accessToken)
      setShortlists((current) => current.map((record) => record.id === updated.id ? updated : record))
      setNotes(updated.notes || '')
      setNotice('Notes saved.')
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setSavingId(null)
    }
  }

  const removeShortlist = async (record) => {
    if (deletingId) return
    setDeletingId(record.id)
    setError('')
    setNotice('')
    try {
      await deleteShortlist(record.id, accessToken)
      setShortlists((current) => current.filter((item) => item.id !== record.id))
      setSelectedId(null)
      setNotes('')
      setNotice(`Candidate #${record.candidate_id} was removed from the shortlist.`)
    } catch (requestError) {
      setError(requestError instanceof ApiError && requestError.status === 404 ? 'Shortlist entry was not found or is no longer available.' : requestError.message)
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <AppShell title="Hiring Dashboard">
      <PageContainer>
        <div className="border-b border-slate-200 pb-6">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Hiring</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Shortlisted Candidates</h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-600">Review recruiter-owned shortlist records and maintain notes.</p>
        </div>
        {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {notice ? <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{notice}</p> : null}

        <Card className="p-5">
          <label className="block max-w-xl text-sm font-medium text-slate-700">
            Filter by Job
            <select value={selectedJobId} disabled={jobsLoading} onChange={(event) => changeJob(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm">
              <option value="">{jobsLoading ? 'Loading jobs...' : 'All jobs'}</option>
              {jobs.map((job) => <option key={job.id} value={job.id}>{job.title}</option>)}
            </select>
          </label>
        </Card>

        <section className="grid gap-4 md:grid-cols-2">
          <Card className="p-5"><p className="text-sm text-slate-500">Total Shortlisted</p><p className="mt-3 text-3xl font-bold text-slate-900">{summary.total}</p></Card>
          <Card className="p-5"><p className="text-sm text-slate-500">Strong Matches</p><p className="mt-3 text-3xl font-bold text-slate-900">{summary.strong}</p></Card>
        </section>

        <Card className="overflow-hidden">
          {loading ? <p className="p-5 text-sm text-slate-600">Loading shortlist...</p> : shortlists.length === 0 ? <p className="p-8 text-center text-sm text-slate-500">No shortlisted candidates found.</p> : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-700">
                <thead className="bg-slate-50 text-slate-600"><tr><th className="px-4 py-3 font-medium">Candidate</th><th className="px-4 py-3 font-medium">Role</th><th className="px-4 py-3 font-medium">Match</th><th className="px-4 py-3 font-medium">Shortlisted</th><th className="px-4 py-3 font-medium">Actions</th></tr></thead>
                <tbody>{shortlists.map((record) => {
                  const percentage = scorePercent(record.match_score)
                  const job = jobs.find((item) => item.id === record.job_id)
                  return <tr key={record.id} className="border-t border-slate-200"><td className="px-4 py-4"><button type="button" className="text-left font-semibold text-slate-900 hover:text-brand-700" onClick={() => selectRecord(record)}>{record.candidate?.full_name || `Candidate #${record.candidate_id}`}</button><div className="text-xs text-slate-500">{record.candidate?.email || `Candidate #${record.candidate_id}`}</div></td><td className="px-4 py-4">{job?.title || `Job #${record.job_id}`}</td><td className="px-4 py-4">{percentage === null ? '—' : `${percentage}%`}</td><td className="px-4 py-4">{record.created_at ? new Date(record.created_at).toLocaleDateString() : '—'}</td><td className="px-4 py-4"><Button type="button" variant="secondary" className="px-3 py-2 text-xs" onClick={() => selectRecord(record)}>Review</Button></td></tr>
                })}</tbody>
              </table>
            </div>
          )}
        </Card>

        {selected ? <Card className="p-5"><div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between"><div><div className="text-xs uppercase tracking-[0.18em] text-brand-700">Candidate Review</div><h2 className="mt-2 text-xl font-semibold text-slate-900">{selected.candidate?.full_name || `Candidate #${selected.candidate_id}`}</h2><p className="mt-1 text-sm text-slate-600">{selected.candidate?.email || `Candidate #${selected.candidate_id}`} · {selectedJob?.title || `Job #${selected.job_id}`}</p></div><Button type="button" variant="ghost" onClick={() => removeShortlist(selected)} disabled={deletingId === selected.id}>{deletingId === selected.id ? 'Removing...' : 'Remove from Shortlist'}</Button></div><div className="mt-5 grid gap-4 md:grid-cols-3 text-sm text-slate-700"><div><span className="text-slate-500">Match score:</span> {scorePercent(selected.match_score) === null ? '—' : `${scorePercent(selected.match_score)}%`}</div><div><span className="text-slate-500">Created:</span> {selected.created_at ? new Date(selected.created_at).toLocaleString() : '—'}</div><div><span className="text-slate-500">Updated:</span> {selected.updated_at ? new Date(selected.updated_at).toLocaleString() : '—'}</div></div><label className="mt-5 block text-sm font-medium text-slate-700">Notes<textarea value={notes} maxLength={2000} onChange={(event) => setNotes(event.target.value)} rows={5} className="mt-2 w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm" /><span className="mt-1 block text-xs text-slate-500">{notes.length}/2000</span></label><Button type="button" className="mt-3" onClick={saveNotes} disabled={savingId === selected.id}>{savingId === selected.id ? 'Saving...' : 'Save Notes'}</Button></Card> : null}
      </PageContainer>
    </AppShell>
  )
}
