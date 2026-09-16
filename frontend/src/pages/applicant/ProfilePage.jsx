import { ApplicantLayout } from '../../app/layouts/ApplicantLayout'
import { applicantProfile } from '../../data/applicantMockData'

export function ProfilePage() {
  return (
    <ApplicantLayout>
      <div className="space-y-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Profile</p>
          <h2 className="mt-2 text-3xl font-bold text-slate-900">Your profile</h2>
        </div>

        <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
          <div className="rounded-3xl border border-slate-200 bg-white p-5">
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-100 text-xl font-bold text-brand-700">
                {applicantProfile.name
                  .split(' ')
                  .map((word) => word[0])
                  .slice(0, 2)
                  .join('')}
              </div>

              <div>
                <h3 className="text-xl font-semibold text-slate-900">{applicantProfile.name}</h3>
                <p className="text-sm text-slate-500">{applicantProfile.role}</p>
              </div>
            </div>

            <div className="mt-6 space-y-3 text-sm text-slate-600">
              <p><span className="font-medium text-slate-800">Email:</span> {applicantProfile.email}</p>
              <p><span className="font-medium text-slate-800">Focus:</span> Product analytics and AI-enabled decision systems</p>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5">
            <h3 className="text-lg font-semibold text-slate-900">Professional summary</h3>
            <p className="mt-3 text-sm leading-7 text-slate-600">{applicantProfile.summary}</p>
          </div>
        </div>
      </div>
    </ApplicantLayout>
  )
}
