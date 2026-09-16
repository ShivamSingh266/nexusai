export function ReadinessGauge({ score = 0, label = 'Readiness' }) {
  const radius = 52
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4">
      <svg width="120" height="120" viewBox="0 0 140 140" className="-rotate-90">
        <circle cx="70" cy="70" r={radius} stroke="#e2e8f0" strokeWidth="12" fill="none" />
        <circle
          cx="70"
          cy="70"
          r={radius}
          stroke="#2563eb"
          strokeWidth="12"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>

      <div>
        <p className="text-sm text-slate-500">{label}</p>
        <p className="text-3xl font-bold text-slate-900">{score}%</p>
      </div>
    </div>
  )
}
