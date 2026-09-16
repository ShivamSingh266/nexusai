import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { NotificationCenter } from './NotificationCenter'
import { SearchCommand } from './SearchCommand'
import { cn } from '../../lib/utils'
import { auth } from '../../services/auth'
import { Menu } from 'lucide-react'

function IconBell() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4">
      <path d="M15 17h5l-1.4-1.5A2 2 0 0118 14.2V11a6 6 0 10-12 0v3.2a2 2 0 01-.6 1.3L4 17h5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M10 20a2 2 0 004 0" strokeLinecap="round" />
    </svg>
  )
}

function IconMoon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4">
      <path d="M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function IconSun() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" strokeLinecap="round" />
    </svg>
  )
}

function IconLogout() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4">
      <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M16 17l5-5-5-5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M21 12H9" strokeLinecap="round" />
    </svg>
  )
}

function IconUser() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-5 w-5">
      <circle cx="12" cy="8" r="4" />
      <path d="M4 20c1.4-3 4.2-4.5 8-4.5s6.6 1.5 8 4.5" strokeLinecap="round" />
    </svg>
  )
}

import { initialNotifications } from '../../mocks/notificationMockData'

export function TopNavbar({ title = 'Dashboard', theme = 'light', onThemeToggle = () => {}, onMenuToggle = () => {}, navigationItems = [] }) {
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const navigate = useNavigate()
  const currentUser = useMemo(() => auth.getUser(), [])

  const [notifications, setNotifications] = useState(() => {
    const role = currentUser?.role || 'applicant'
    return initialNotifications.filter((n) => !n.role || n.role === role || role === 'admin')
  })

  const markAllRead = () => {
    setNotifications((current) => current.map((item) => ({ ...item, read: true })))
  }

  const markOneRead = (id) => {
    setNotifications((current) =>
      current.map((item) => (item.id === id ? { ...item, read: true } : item)),
    )
  }

  const handleLogout = () => {
    auth.logout()
    navigate('/login')
  }

  const roleLabel = {
    applicant: 'Applicant',
    recruiter: 'Recruiter',
    government: 'Government',
    admin: 'Admin',
  }[currentUser?.role] || 'User'

  return (
    <header className={cn('sticky top-0 z-20 border-b backdrop-blur-xl', theme === 'dark' ? 'border-slate-700 bg-slate-950/80' : 'border-slate-200 bg-white/80')}>
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-4">
          <button
            type="button"
            onClick={onMenuToggle}
            className={cn(
              'inline-flex h-10 w-10 items-center justify-center rounded-full border xl:hidden',
              theme === 'dark' ? 'border-slate-700 bg-slate-900 text-slate-200' : 'border-slate-200 bg-white text-slate-700',
            )}
            aria-label="Open navigation"
          >
            <Menu className="h-4 w-4" />
          </button>
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 to-brand-800 text-sm font-bold text-white shadow-sm">
            N
          </div>

          <div className="min-w-0">
            <p className="truncate text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">
              NexusAI
            </p>
            <h1 className={cn('truncate text-lg font-bold', theme === 'dark' ? 'text-slate-100' : 'text-slate-900')}>{title}</h1>
          </div>
        </div>

        <div className="hidden flex-1 justify-center md:flex">
          <SearchCommand items={navigationItems} theme={theme} />
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <button
            type="button"
            onClick={onThemeToggle}
            className={cn(
              'inline-flex h-10 w-10 items-center justify-center rounded-full border transition',
              theme === 'dark' ? 'border-slate-700 bg-slate-900 text-slate-200 hover:bg-slate-800' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50 hover:text-slate-900',
            )}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <IconSun /> : <IconMoon />}
          </button>

          <div className="relative">
            <button
              type="button"
              onClick={() => {
                setNotificationsOpen((current) => !current)
                if (notificationsOpen) {
                  markAllRead()
                }
              }}
              className={cn(
                'relative inline-flex h-10 w-10 items-center justify-center rounded-full border transition',
                theme === 'dark'
                  ? 'border-slate-700 bg-slate-900 text-slate-200 hover:bg-slate-800'
                  : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50 hover:text-slate-900',
                notificationsOpen && (theme === 'dark' ? 'border-brand-500/40 bg-brand-500/10 text-brand-300' : 'border-brand-200 bg-brand-50 text-brand-700'),
              )}
              aria-label="Notifications"
            >
              <IconBell />
              {notifications.some((notification) => !notification.read) && (
                <span className="absolute -right-1 -top-1 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-brand-600 px-1 text-[10px] font-bold text-white">
                  {notifications.filter((notification) => !notification.read).length}
                </span>
              )}
            </button>

            <NotificationCenter
              notifications={notifications}
              isOpen={notificationsOpen}
              onClose={() => setNotificationsOpen(false)}
              onMarkAsRead={markOneRead}
              onMarkAllRead={markAllRead}
            />
          </div>

          <div className={cn('hidden items-center gap-3 rounded-full border px-2 py-1.5 sm:flex', theme === 'dark' ? 'border-slate-700 bg-slate-900' : 'border-slate-200 bg-white')}>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-brand-700">
              <IconUser />
            </div>
            <div className="text-left">
              <p className={cn('text-sm font-semibold', theme === 'dark' ? 'text-slate-100' : 'text-slate-900')}>{currentUser?.full_name || currentUser?.name || 'NexusAI User'}</p>
              <p className={cn('text-[11px]', theme === 'dark' ? 'text-slate-400' : 'text-slate-500')}>{roleLabel}</p>
            </div>
          </div>

          <button
            type="button"
            onClick={handleLogout}
            className={cn('inline-flex items-center gap-2 rounded-full border px-3 py-2 text-sm font-medium transition', theme === 'dark' ? 'border-slate-700 bg-slate-900 text-slate-100 hover:bg-slate-800' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50')}
          >
            <IconLogout />
            <span className="hidden sm:inline">Logout</span>
          </button>
        </div>
      </div>
    </header>
  )
}
