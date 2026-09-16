import { cn } from '../../lib/utils'

export function ComparisonBarChart({
  data = [],
  series = [
    { key: 'demand', label: 'Market Demand', color: '#2563eb' },
    { key: 'alignment', label: 'Curriculum Alignment', color: '#10b981' },
  ],
  max = 100,
  className = '',
}) {
  if (!data || data.length === 0) {
    return (
      <div className={cn('flex items-center justify-center p-6 text-sm text-slate-400', className)}>
        No comparison data available
      </div>
    )
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 text-xs font-medium text-slate-600">
        {series.map((s) => (
          <div key={s.key} className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-sm" style={{ backgroundColor: s.color }} />
            <span>{s.label}</span>
          </div>
        ))}
      </div>

      {/* Comparison Bars */}
      <div className="space-y-4">
        {data.map((item, idx) => (
          <div key={item.label || idx} className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
              <span>{item.label}</span>
              <span className="text-slate-400 text-[11px]">
                {series.map((s) => `${s.label}: ${item[s.key] ?? 0}%`).join(' | ')}
              </span>
            </div>

            <div className="space-y-1">
              {series.map((s) => {
                const val = Math.min(Math.max(item[s.key] ?? 0, 0), max)
                const percentage = (val / max) * 100

                return (
                  <div key={s.key} className="relative h-3 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full transition-all duration-500 ease-out"
                      style={{
                        width: `${percentage}%`,
                        backgroundColor: s.color,
                      }}
                      title={`${s.label}: ${val}%`}
                    />
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ComparisonBarChart
