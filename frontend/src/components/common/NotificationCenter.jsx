import { useEffect, useMemo, useRef } from 'react'
import { CheckCheck, X, Bell } from 'lucide-react'
import { cn } from '../../lib/utils'

export function NotificationCenter({
  notifications = [],
  isOpen = false,
  onClose,
  onMarkAsRead,
  onMarkAllRead,
}) {
  const dropdownRef = useRef(null)

  const unreadCount = useMemo(
    () => notifications.filter((notification) => !notification.read).length,
    [notifications],
  )

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return

    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        onClose?.()
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen, onClose])

  if (!isOpen) {
    return null
  }

  return (
    <div
      ref={dropdownRef}
      className="absolute right-0 top-full z-40 mt-3 w-80 sm:w-96 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl ring-1 ring-slate-900/5 transition-all animate-in fade-in slide-in-from-top-2 duration-150"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3.5 bg-slate-50/50">
        <div className="flex items-center gap-2">
          <Bell className="h-4 w-4 text-brand-600" />
          <span className="text-sm font-semibold text-slate-900">Notifications</span>
          {unreadCount > 0 && (
            <span className="rounded-full bg-brand-100 px-2 py-0.5 text-xs font-semibold text-brand-700">
              {unreadCount} new
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <button
              type="button"
              className="inline-flex items-center gap-1 text-xs font-medium text-brand-700 hover:text-brand-800 transition"
              onClick={onMarkAllRead}
            >
              <CheckCheck className="h-3.5 w-3.5" />
              Mark all read
            </button>
          )}

          <button
            type="button"
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition"
            onClick={onClose}
            aria-label="Close notifications"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Notifications list */}
      <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
        {notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center px-4 py-10 text-center">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-400 mb-2">
              <Bell className="h-5 w-5" />
            </div>
            <p className="text-sm font-medium text-slate-700">No notifications yet</p>
            <p className="mt-1 text-xs text-slate-500">We'll alert you when matching updates arrive.</p>
          </div>
        ) : (
          notifications.map((notification) => (
            <button
              key={notification.id}
              type="button"
              onClick={() => onMarkAsRead?.(notification.id)}
              className={cn(
                'flex w-full items-start gap-3 px-4 py-3 text-left transition hover:bg-slate-50',
                !notification.read ? 'bg-brand-50/40 hover:bg-brand-50/70' : 'bg-white',
              )}
            >
              <span
                className={cn(
                  'mt-1.5 h-2 w-2 shrink-0 rounded-full',
                  notification.read ? 'bg-transparent' : 'bg-brand-600 ring-2 ring-brand-200',
                )}
              />

              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <p className={cn('text-xs font-semibold', notification.read ? 'text-slate-700' : 'text-slate-900')}>
                    {notification.title}
                  </p>
                  <span className="text-[10px] whitespace-nowrap text-slate-400 font-medium">
                    {notification.time}
                  </span>
                </div>
                <p className="mt-1 text-xs leading-relaxed text-slate-600">{notification.message}</p>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  )
}

export default NotificationCenter
