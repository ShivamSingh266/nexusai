import { useState } from 'react'
import { cn } from '../../lib/utils'

export function LineTrendChart({
  data = [],
  axes = true,
  tooltip = true,
  height = 180,
  strokeColor = '#2563eb',
  fillColor = '#3b82f6',
  className = '',
}) {
  const [hoveredPoint, setHoveredPoint] = useState(null)

  if (!data || data.length === 0) {
    return (
      <div className={cn('flex items-center justify-center text-sm text-slate-400', className)} style={{ height }}>
        No trend data available
      </div>
    )
  }

  // Normalize data objects to { label, value }
  const normalizedData = data.map((d, index) => {
    if (typeof d === 'number') {
      return { label: `Point ${index + 1}`, value: d }
    }
    return { label: d.label || d.month || `P${index + 1}`, value: d.value ?? 0 }
  })

  const values = normalizedData.map((d) => d.value)
  const maxVal = Math.max(...values, 1)
  const minVal = Math.min(...values, 0)
  const range = maxVal - minVal || 1

  const paddingX = 40
  const paddingY = 30
  const svgWidth = 500
  const svgHeight = height

  const graphWidth = svgWidth - paddingX * 2
  const graphHeight = svgHeight - paddingY * 2

  const points = normalizedData.map((d, index) => {
    const x = paddingX + (index / (normalizedData.length - 1 || 1)) * graphWidth
    const y = paddingY + graphHeight - ((d.value - minVal) / range) * graphHeight
    return { ...d, x, y }
  })

  const pathD = points.reduce((acc, point, index) => {
    return index === 0 ? `M ${point.x} ${point.y}` : `${acc} L ${point.x} ${point.y}`
  }, '')

  const areaD = `${pathD} L ${points[points.length - 1].x} ${paddingY + graphHeight} L ${points[0].x} ${paddingY + graphHeight} Z`

  return (
    <div className={cn('relative w-full overflow-hidden', className)}>
      <svg
        viewBox={`0 0 ${svgWidth} ${svgHeight}`}
        className="h-full w-full overflow-visible"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="lineTrendGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={fillColor} stopOpacity="0.25" />
            <stop offset="100%" stopColor={fillColor} stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Axes & Grid lines */}
        {axes && (
          <g className="text-slate-200">
            {/* Horizontal grid lines */}
            {[0, 0.5, 1].map((ratio) => {
              const y = paddingY + graphHeight * ratio
              const labelValue = Math.round(maxVal - ratio * range)
              return (
                <g key={ratio}>
                  <line
                    x1={paddingX}
                    y1={y}
                    x2={paddingX + graphWidth}
                    y2={y}
                    stroke="currentColor"
                    strokeDasharray="4 4"
                    strokeWidth="1"
                  />
                  <text
                    x={paddingX - 8}
                    y={y + 4}
                    textAnchor="end"
                    className="fill-slate-400 text-[10px]"
                  >
                    {labelValue}
                  </text>
                </g>
              )
            })}
          </g>
        )}

        {/* Area fill */}
        <path d={areaD} fill="url(#lineTrendGrad)" />

        {/* Line stroke */}
        <path
          d={pathD}
          fill="none"
          stroke={strokeColor}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Interactive circles */}
        {points.map((pt, i) => (
          <g key={i} className="cursor-pointer">
            <circle
              cx={pt.x}
              cy={pt.y}
              r={hoveredPoint === i ? 6 : 3.5}
              fill={hoveredPoint === i ? strokeColor : '#ffffff'}
              stroke={strokeColor}
              strokeWidth="2"
              className="transition-all duration-150"
              onMouseEnter={() => setHoveredPoint(i)}
              onMouseLeave={() => setHoveredPoint(null)}
            />
          </g>
        ))}

        {/* X-axis labels */}
        {axes &&
          points.map((pt, i) => (
            <text
              key={i}
              x={pt.x}
              y={svgHeight - 8}
              textAnchor="middle"
              className="fill-slate-500 text-[11px] font-medium"
            >
              {pt.label}
            </text>
          ))}
      </svg>

      {/* Floating tooltip */}
      {tooltip && hoveredPoint !== null && points[hoveredPoint] && (
        <div
          className="pointer-events-none absolute -translate-x-1/2 -translate-y-full rounded-lg border border-slate-700 bg-slate-900 px-2.5 py-1 text-xs text-white shadow-lg transition-all"
          style={{
            left: `${(points[hoveredPoint].x / svgWidth) * 100}%`,
            top: `${(points[hoveredPoint].y / svgHeight) * 100 - 8}%`,
          }}
        >
          <div className="font-semibold">{points[hoveredPoint].label}</div>
          <div className="text-slate-300">Value: {points[hoveredPoint].value}</div>
        </div>
      )}
    </div>
  )
}

export default LineTrendChart
