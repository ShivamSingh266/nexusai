import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppShell } from '../../components/layout/AppShell'
import { PageContainer } from '../../components/layout/PageContainer'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StatCard } from '../../components/hiring/StatCard'
import { StatusBadge } from '../../components/hiring/StatusBadge'
import { useAuth } from '../../auth/AuthContext'
import { listJobs } from '../../services/recruiter'

const statusLabel = {
  draft: 'Draft',
  published: 'Published',
  closed: 'Closed',
}

export function HiringDashboardPage() {
  const { accessToken } = useAuth()
  const navigate = useNavigate()
  const [jobs, setJobs] = useState([])
  const [pagination, setPagination] = useState({ total: 0, page: 1, page_size: 20, total_pages: 0 })
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    listJobs(accessToken, { page, page_size: 20 })
      .then((response) => {
        if (active) {
          setJobs(response.data)
          setPagination({
            total: response.total,
            page: response.page,
            page_size: response.page_size,
            total_pages: response.total_pages,
          })
        }
      })
      .catch((requestError) => { if (active) setError(requestError.message) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [accessToken, page])

  const changePage = (nextPage) => {
    setLoading(true)
    setError('')
    setPage(nextPage)
  }

  const kpis = useMemo(() => [
    { label: 'Total Jobs', value: pagination.total, change: 'All recruiter jobs' },
    { label: 'Published Jobs', value: jobs.filter((job) => job.status === 'published').length, change: 'On this page' },
    { label: 'Draft Jobs', value: jobs.filter((job) => job.status === 'draft').length, change: 'On this page' },
    { label: 'Closed Jobs', value: jobs.filter((job) => job.status === 'closed').length, change: 'On this page' },
  ], [jobs, pagination.total])

  return (
    <AppShell title="Hiring Dashboard">
      <PageContainer>
        <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Hiring</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Hiring Dashboard</h1>
            <p className="mt-2 max-w-xl text-sm text-slate-600">Manage your company’s job postings and hiring workspace.</p>
          </div>
          <Button onClick={() => navigate('/hiring/post-job')}>Post a Job</Button>
        </div>

        {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {kpis.map((item) => <StatCard key={item.label} label={item.label} value={item.value} change={item.change} />)}
        </section>

        <Card className="overflow-hidden">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
            <h2 className="text-lg font-semibold text-slate-900">Your Jobs</h2>
            <Button variant="secondary" className="px-3 py-2 text-xs" onClick={() => navigate('/hiring/post-job')}>Create job</Button>
          </div>
          {loading ? <p className="p-5 text-sm text-slate-600">Loading jobs...</p> : jobs.length === 0 ? <p className="p-5 text-sm text-slate-600">No jobs found. Create your first job posting.</p> : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-700">
                <thead className="bg-slate-50 text-slate-600"><tr><th className="px-5 py-3 font-medium">Job Title</th><th className="px-5 py-3 font-medium">Location</th><th className="px-5 py-3 font-medium">Work Mode</th><th className="px-5 py-3 font-medium">Status</th><th className="px-5 py-3 font-medium">Created</th></tr></thead>
                <tbody>{jobs.map((job) => <tr key={job.id} className="border-t border-slate-200"><td className="px-5 py-4 font-medium text-slate-900">{job.title}</td><td className="px-5 py-4">{job.location || job.districts?.join(', ') || 'Not specified'}</td><td className="px-5 py-4">{job.work_mode || 'Not specified'}</td><td className="px-5 py-4"><StatusBadge status={statusLabel[job.status] || job.status} /></td><td className="px-5 py-4">{job.created_at ? new Date(job.created_at).toLocaleDateString() : '—'}</td></tr>)}</tbody>
              </table>
            </div>
          )}
          {!loading && pagination.total_pages > 0 ? (
            <div className="flex items-center justify-between border-t border-slate-200 px-5 py-4 text-sm text-slate-600">
              <span>Showing page {pagination.page} of {pagination.total_pages} ({pagination.total} total jobs)</span>
              <div className="flex gap-2">
                <Button type="button" variant="secondary" className="px-3 py-2 text-xs" disabled={page <= 1} onClick={() => changePage(page - 1)}>Previous</Button>
                <Button type="button" variant="secondary" className="px-3 py-2 text-xs" disabled={page >= pagination.total_pages} onClick={() => changePage(page + 1)}>Next</Button>
              </div>
            </div>
          ) : null}
        </Card>

        <section className="grid gap-6 md:grid-cols-2">
          <Card className="p-5"><h2 className="text-lg font-semibold text-slate-900">Quick Actions</h2><div className="mt-4 grid gap-3"><button type="button" onClick={() => navigate('/hiring/post-job')} className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-left hover:border-brand-200 hover:bg-brand-50"><div className="text-sm font-semibold text-slate-900">Post a Job</div><div className="text-xs text-slate-500">Create a new role</div></button><button type="button" onClick={() => navigate('/hiring/company-profile')} className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-left hover:border-brand-200 hover:bg-brand-50"><div className="text-sm font-semibold text-slate-900">Company Profile</div><div className="text-xs text-slate-500">Update company details</div></button></div></Card>
          <Card className="border-brand-100 bg-gradient-to-br from-brand-50 to-white p-5"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">NexusAI</p><h2 className="mt-3 text-xl font-semibold text-slate-900">Recruiter workspace</h2><p className="mt-2 text-sm text-slate-600">Matching and shortlist workflows remain available for the next integration step.</p></Card>
        </section>
      </PageContainer>
    </AppShell>
  )
}
