export function TrendArrow({ direction = 'up', percentage = 0 }) {
  const isPositive = direction === 'up'

  return (
    <span className={isPositive ? 'text-emerald-600' : 'text-rose-600'}>
      {isPositive ? '↗' : '↘'} {Math.abs(percentage)}%
    </span>
  )
}
