import { cn } from '../../lib/utils'

export function PageContainer({ children, className = '' }) {
  return (
    <div className={cn('space-y-6', className)}>
      {children}
    </div>
  )
}
