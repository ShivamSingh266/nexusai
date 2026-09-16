import { Link } from 'react-router-dom'
import { StatCard } from '../../components/common/StatCard'
import { JobPreviewCard } from '../../components/dashboard/JobPreviewCard'
import { ReadinessGauge } from '../../components/dashboard/ReadinessGauge'
import { RoadmapProgressCard } from '../../components/dashboard/RoadmapProgressCard'
import { InterviewReminderCard } from '../../components/dashboard/InterviewReminderCard'
import { MarketSparkline } from '../../components/dashboard/MarketSparkline'
import { applicantDashboardStats, applicantJobs, applicantInsights } from '../../data/applicantMockData'

export function DashboardPage() {
  return (
    <div className="space-y-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Overview</p>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Applicant dashboard</h2>
          </div>

          <Link to="/applicant/jobs" className="inline-flex items-center rounded-full bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700">
            Explore jobs
          </Link>
        </div>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {applicantDashboardStats.map((stat) => (
            <StatCard
              key={stat.title}
              title={stat.title}
              value={stat.value}
              subtitle={stat.subtitle}
              icon={stat.icon}
              trend={stat.trend}
              variant={stat.variant}
            />
          ))}
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
          <div className="space-y-6">
            <div className="rounded-3xl border border-slate-200 bg-white p-5">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900">Career momentum</h3>
                <span className="text-sm font-medium text-brand-700">+12.4%</span>
              </div>
              <MarketSparkline data={applicantInsights.trend} color="#2563eb" />
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900">Recommended roles</h3>
                <Link to="/applicant/jobs" className="text-sm font-semibold text-brand-700">View all</Link>
              </div>

              <div className="grid gap-4 lg:grid-cols-3">
                {applicantJobs.map((job) => (
                  <JobPreviewCard
                    key={job.title}
                    title={job.title}
                    company={job.company}
                    location={job.location}
                    salary={job.salary}
                    matchScore={job.matchScore}
                  />
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <ReadinessGauge score={84} label="Profile readiness" />
            <RoadmapProgressCard completed={2} remaining={2} total={4} />
            <InterviewReminderCard interviewDate="Sat, 10:30 AM" role="Data Analyst interview" />
          </div>
        </section>
      </div>
  )
}
