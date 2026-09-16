export function InterviewReminderCard({ interviewDate, role, ctaLabel = 'View details' }) {
  return (
    <div className="rounded-2xl border border-brand-200 bg-brand-50 p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Interview</p>
      <h3 className="mt-2 text-lg font-semibold text-slate-900">{role}</h3>
      <p className="mt-2 text-sm text-slate-600">Scheduled for {interviewDate}</p>
      <button type="button" className="mt-4 rounded-full bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700">
        {ctaLabel}
      </button>
    </div>
  )
}
