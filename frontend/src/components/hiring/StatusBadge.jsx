export function StatusBadge({ status }) {
  const toneMap = {
    Hiring: 'bg-emerald-100 text-emerald-700',
    Reviewing: 'bg-amber-100 text-amber-700',
    Interviewing: 'bg-blue-100 text-blue-700',
    Shortlisting: 'bg-violet-100 text-violet-700',
    'Interview Ready': 'bg-emerald-100 text-emerald-700',
    'Strong Match': 'bg-blue-100 text-blue-700',
    Shortlisted: 'bg-violet-100 text-violet-700',
    'In Progress': 'bg-amber-100 text-amber-700',
  }

  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${
        toneMap[status] || 'bg-slate-100 text-slate-700'
      }`}
    >
      {status}
    </span>
  )
}
