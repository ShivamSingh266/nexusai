import { useMemo } from 'react'
import { cn } from '../../lib/utils'

export function GaugeChart({
  score = 0,
  min = 0,
  max = 100,
  thresholds = [
    { value: 40, color: '#f43f5e' }, // rose-500
    { value: 70, color: '#f59e0b' }, // amber-500
    { value: 100, color: '#10b981' }, // emerald-500
  ],
  size = 180,
  strokeWidth = 14,
  label = 'Score',
  className = '',
}) {
  const normalizedScore = Math.min(Math.max(score, min), max)
  const percentage = ((normalizedScore - min) / (max - min)) * 100

  // Semi-circle gauge (180 degrees arc)
  const radius = (size - strokeWidth) / 2
  const arcLength = Math.PI * radius
  const strokeDashoffset = arcLength - (percentage / 100) * arcLength

  const activeColor = useMemo(() => {
    for (const threshold of thresholds) {
      if (normalizedScore <= threshold.value) {
        return threshold.color
      }
    }
    return thresholds[thresholds.length - 1]?.color || '#2563eb'
  }, [normalizedScore, thresholds])

  return (
    <div className={cn('flex flex-col items-center justify-center', className)}>
      <div className="relative" style={{ width: size, height: size / 2 + 20 }}>
        <svg width={size} height={size / 2 + 10} viewBox={`0 0 ${size} ${size / 2 + 10}`}>
          {/* Background Track */}
          <path
            d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${size / 2}`}
            fill="none"
            stroke="#e2e8f0"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
          {/* Active Value Arc */}
          <path
            d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${size / 2}`}
            fill="none"
            stroke={activeColor}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={arcLength}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-700 ease-out"
          />
        </svg>

        {/* Center label & score */}
        <div className="absolute inset-x-0 bottom-0 flex flex-col items-center justify-center text-center">
          <span className="text-2xl font-bold tracking-tight text-slate-900">{normalizedScore}%</span>
          {label && <span className="text-xs font-medium text-slate-500">{label}</span>}
        </div>
      </div>
    </div>
  )
}

export default GaugeChart
