import { useNavigate } from 'react-router-dom'
import { AppShell } from '../../components/layout/AppShell'
import { PageContainer } from '../../components/layout/PageContainer'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StatCard } from '../../components/hiring/StatCard'
import { StatusBadge } from '../../components/hiring/StatusBadge'
import { activeJobs, hiringKpis, quickActions, recentCandidates } from '../../mocks/hiringMockData'

export function HiringDashboardPage() {
  const navigate = useNavigate()

  return (
    <AppShell title="Hiring Dashboard">
      <PageContainer>
        <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Hiring</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Hiring Dashboard</h1>
            <p className="mt-2 max-w-xl text-sm text-slate-600">
              Track active roles, candidate pipeline health, and hiring momentum across the team.
            </p>
          </div>

          <Button onClick={() => navigate('/hiring/post-job')}>Post a Job</Button>
        </div>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {hiringKpis.map((item) => (
            <StatCard key={item.label} label={item.label} value={item.value} change={item.change} />
          ))}
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.6fr_0.9fr]">
          <Card className="overflow-hidden">
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Active Jobs</h2>
              </div>
              <Button variant="secondary" className="px-3 py-2 text-xs">
                View all
              </Button>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-700">
                <thead className="bg-slate-50 text-slate-600">
                  <tr>
                    <th className="px-5 py-3 font-medium">Job Title</th>
                    <th className="px-5 py-3 font-medium">Department</th>
                    <th className="px-5 py-3 font-medium">Applicants</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3 font-medium">Posted</th>
                    <th className="px-5 py-3 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {activeJobs.map((job) => (
                    <tr key={job.title} className="border-t border-slate-200">
                      <td className="px-5 py-4 font-medium text-slate-900">{job.title}</td>
                      <td className="px-5 py-4">{job.department}</td>
                      <td className="px-5 py-4">{job.applicants}</td>
                      <td className="px-5 py-4">
                        <StatusBadge status={job.status} />
                      </td>
                      <td className="px-5 py-4">{job.postedDate}</td>
                      <td className="px-5 py-4">
                        <button className="font-medium text-brand-700 hover:text-brand-800">
                          {job.action}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card className="p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Quick Actions</h2>
            </div>

            <div className="mt-4 grid gap-3">
              {quickActions.map((action) => (
                <button
                  key={action.label}
                  type="button"
                  onClick={() => {
                    if (action.path) {
                      navigate(action.path)
                    }
                  }}
                  className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-left transition hover:border-brand-200 hover:bg-brand-50"
                >
                  <div>
                    <div className="text-sm font-semibold text-slate-900">{action.label}</div>
                    <div className="text-xs text-slate-500">{action.value}</div>
                  </div>
                  <span className="text-lg text-slate-400">→</span>
                </button>
              ))}
            </div>
          </Card>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <Card className="p-5">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Recent Candidates</h2>
              <Button variant="ghost" className="px-3 py-2 text-xs">
                View all
              </Button>
            </div>

            <div className="space-y-3">
              {recentCandidates.map((candidate) => (
                <div
                  key={candidate.name}
                  className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <div className="font-semibold text-slate-900">{candidate.name}</div>
                    <div className="text-sm text-slate-500">{candidate.role}</div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 sm:justify-end">
                    <span className="rounded-full bg-brand-50 px-2.5 py-1 text-xs font-semibold text-brand-700">
                      {candidate.match}
                    </span>
                    <StatusBadge status={candidate.status} />
                    <span className="text-xs text-slate-500">{candidate.stage}</span>
                    <button className="text-xs font-semibold text-brand-700 hover:text-brand-800">
                      {candidate.action}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="overflow-hidden border-brand-100 bg-gradient-to-br from-brand-50 to-white p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">NexusAI</p>
            <h2 className="mt-3 text-xl font-semibold text-slate-900">AI Candidate Matching</h2>
            <p className="mt-2 text-sm text-slate-600">
              Surface the best-fit talent faster with intelligent role-to-candidate signal matching,
              skills alignment, and hiring priority scoring.
            </p>

            <div className="mt-5 space-y-3">
              <div className="rounded-xl border border-brand-100 bg-white/80 p-3">
                <div className="flex items-center justify-between text-sm text-slate-600">
                  <span>Role fit</span>
                  <span className="font-semibold text-slate-900">96%</span>
                </div>
                <div className="mt-2 h-2 rounded-full bg-slate-200">
                  <div className="h-2 w-[96%] rounded-full bg-brand-600" />
                </div>
              </div>

              <div className="rounded-xl border border-brand-100 bg-white/80 p-3">
                <div className="flex items-center justify-between text-sm text-slate-600">
                  <span>Skill match</span>
                  <span className="font-semibold text-slate-900">91%</span>
                </div>
                <div className="mt-2 h-2 rounded-full bg-slate-200">
                  <div className="h-2 w-[91%] rounded-full bg-brand-500" />
                </div>
              </div>
            </div>
          </Card>
        </section>
      </PageContainer>
    </AppShell>
  )
}
