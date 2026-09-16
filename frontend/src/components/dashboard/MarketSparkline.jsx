export function MarketSparkline({ data = [], color = '#2563eb' }) {
  if (!data.length) return null

  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1

  const points = data
    .map((value, index) => {
      const x = (index / (data.length - 1)) * 100
      const y = 100 - ((value - min) / range) * 100
      return `${x},${y}`
    })
    .join(' ')

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="h-24 w-full">
        <defs>
          <linearGradient id="sparklineGradient" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.35" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>

        <polyline
          fill="none"
          stroke={color}
          strokeWidth="3"
          points={points}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  )
}
