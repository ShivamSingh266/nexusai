import { cn } from '../../lib/utils'

export function ProgressRing({
  percentage = 0,
  size = 80,
  strokeWidth = 8,
  color = '#2563eb',
  trackColor = '#e2e8f0',
  showValue = true,
  label,
  className = '',
}) {
  const normalizedPercentage = Math.min(Math.max(percentage, 0), 100)
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (normalizedPercentage / 100) * circumference

  return (
    <div className={cn('inline-flex flex-col items-center justify-center', className)}>
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={trackColor}
            strokeWidth={strokeWidth}
            fill="none"
          />
          {/* Active progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-500 ease-out"
          />
        </svg>

        {showValue && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-sm font-bold tracking-tight text-slate-900">
              {Math.round(normalizedPercentage)}%
            </span>
          </div>
        )}
      </div>

      {label && <span className="mt-1 text-xs font-medium text-slate-600">{label}</span>}
    </div>
  )
}

export default ProgressRing
