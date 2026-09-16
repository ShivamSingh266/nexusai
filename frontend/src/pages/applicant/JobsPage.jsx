import { ApplicantLayout } from '../../app/layouts/ApplicantLayout'
import { JobPreviewCard } from '../../components/dashboard/JobPreviewCard'
import { applicantJobs } from '../../data/applicantMockData'

export function JobsPage() {
  return (
    <ApplicantLayout>
      <div className="space-y-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Jobs</p>
          <h2 className="mt-2 text-3xl font-bold text-slate-900">Recommended jobs</h2>
        </div>

        <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
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
    </ApplicantLayout>
  )
}
