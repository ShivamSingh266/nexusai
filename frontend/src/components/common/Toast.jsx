import { useEffect, useState } from 'react'
import { cn } from '../../lib/utils'

export function Toast({ variant = 'info', title, message, duration = 3000, onDismiss }) {
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false)
      onDismiss?.()
    }, duration)

    return () => clearTimeout(timer)
  }, [duration, onDismiss])

  if (!visible) return null

  const styles = {
    success: 'border-emerald-200 bg-emerald-50 text-emerald-900',
    error: 'border-rose-200 bg-rose-50 text-rose-900',
    info: 'border-brand-200 bg-brand-50 text-brand-900',
    warning: 'border-amber-200 bg-amber-50 text-amber-900',
  }

  return (
    <div className={cn('max-w-sm rounded-2xl border p-4 shadow-lg', styles[variant])}>
      <div className="flex items-start justify-between gap-3">
        <div>
          {title && <p className="text-sm font-semibold">{title}</p>}
          {message && <p className="mt-1 text-sm opacity-80">{message}</p>}
        </div>

        <button
          type="button"
          className="text-sm font-medium opacity-70 hover:opacity-100"
          onClick={() => {
            setVisible(false)
            onDismiss?.()
          }}
        >
          ×
        </button>
      </div>
    </div>
  )
}
