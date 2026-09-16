export function InterviewPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Interview</p>
        <h2 className="mt-2 text-3xl font-bold text-slate-900">Interview preparation</h2>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-3xl border border-slate-200 bg-white p-5">
          <h3 className="text-lg font-semibold text-slate-900">Upcoming sessions</h3>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            <li className="rounded-xl bg-slate-50 p-3">Mock interview: Saturday, 10:30 AM</li>
            <li className="rounded-xl bg-slate-50 p-3">Case review: Tuesday, 4:00 PM</li>
          </ul>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-5">
          <h3 className="text-lg font-semibold text-slate-900">Focus areas</h3>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            <li>System design basics</li>
            <li>Storytelling for product impact</li>
            <li>SQL optimization</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
