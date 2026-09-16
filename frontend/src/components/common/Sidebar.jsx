import { useMemo } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { LogOut, PanelLeftClose, PanelLeftOpen, User } from 'lucide-react'
import { cn } from '../../lib/utils'
import { auth } from '../../services/auth'

const defaultItems = [
  { label: 'Dashboard', to: '/applicant/dashboard', icon: 'D' },
  { label: 'Profile', to: '/applicant/profile', icon: 'P' },
  { label: 'Resume', to: '/applicant/resume', icon: 'R' },
  { label: 'Skill Gap', to: '/applicant/skill-gap', icon: 'S' },
  { label: 'Market', to: '/applicant/market', icon: 'M' },
  { label: 'Roadmap', to: '/applicant/roadmap', icon: 'O' },
]

export function Sidebar({
  items = defaultItems,
  collapsed = false,
  onToggle = () => {},
  theme = 'light',
  mobileOpen = false,
  onClose = () => {},
}) {
  const dark = theme === 'dark'
  const navigate = useNavigate()
  const user = useMemo(() => auth.getUser(), [])

  const handleLogout = () => {
    auth.logout()
    navigate('/login')
  }

  return (
    <>
      {mobileOpen && (
        <button
          type="button"
          aria-label="Close navigation backdrop"
          onClick={onClose}
          className="fixed inset-0 z-30 bg-slate-950/40 backdrop-blur-sm xl:hidden transition-opacity"
        />
      )}

      <aside
        className={cn(
          'shrink-0 flex flex-col rounded-3xl border p-3 shadow-sm backdrop-blur transition-all duration-300 ease-in-out',
          dark ? 'border-slate-700 bg-slate-900/90' : 'border-slate-200 bg-white/90',
          collapsed ? 'w-[70px]' : 'w-[260px]',
          mobileOpen
            ? 'fixed inset-y-4 left-4 z-40 flex w-[260px] flex-col xl:static'
            : 'hidden xl:flex',
        )}
      >
        {/* Header with collapse toggle */}
        <div className="mb-4 flex items-center justify-between gap-2 px-2 pt-1">
          <div
            className={cn(
              'overflow-hidden whitespace-nowrap transition-all duration-300',
              collapsed ? 'w-0 opacity-0' : 'w-auto opacity-100',
            )}
          >
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-brand-700">
              Workspace
            </p>
            <h2 className={cn('text-base font-bold', dark ? 'text-slate-100' : 'text-slate-900')}>
              NexusAI
            </h2>
          </div>

          <button
            type="button"
            onClick={onToggle}
            className={cn(
              'inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-xs font-semibold transition hover:scale-105',
              dark
                ? 'border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700'
                : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100 hover:text-slate-900',
            )}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <PanelLeftOpen className="h-3.5 w-3.5" /> : <PanelLeftClose className="h-3.5 w-3.5" />}
          </button>
        </div>

        {/* Navigation list */}
        <nav className="flex-1 space-y-1.5 overflow-y-auto pr-0.5">
          {items.map((item) => {
            const itemLabel = item.title || item.label
            const itemPath = item.path || item.to
            const ItemIcon = item.icon

            return (
              <NavLink
                key={itemPath}
                to={itemPath}
                onClick={onClose}
                className={({ isActive }) =>
                  cn(
                    'group relative flex items-center gap-3 rounded-xl px-2.5 py-2 text-sm font-medium transition-all duration-150',
                    isActive
                      ? dark
                        ? 'bg-brand-500/15 text-brand-300 ring-1 ring-brand-500/30 font-semibold'
                        : 'bg-brand-50 text-brand-700 ring-1 ring-brand-200 font-semibold'
                      : dark
                        ? 'text-slate-300 hover:bg-slate-800 hover:text-slate-100'
                        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900',
                    collapsed && 'justify-center px-1.5',
                  )
                }
                title={collapsed ? itemLabel : undefined}
              >
                <span
                  className={cn(
                    'flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-bold transition group-hover:scale-105',
                    dark ? 'bg-slate-800 text-slate-200' : 'bg-slate-100 text-slate-700',
                  )}
                >
                  {typeof ItemIcon === 'string' ? ItemIcon : <ItemIcon className="h-4 w-4" />}
                </span>

                <span
                  className={cn(
                    'overflow-hidden whitespace-nowrap text-xs transition-all duration-300',
                    collapsed ? 'w-0 opacity-0' : 'w-auto opacity-100',
                  )}
                >
                  {itemLabel}
                </span>

                {/* Tooltip on collapsed state hover */}
                {collapsed && (
                  <span className="pointer-events-none absolute left-full z-50 ml-2 hidden rounded-md bg-slate-900 px-2 py-1 text-xs font-medium text-white shadow-md group-hover:block whitespace-nowrap">
                    {itemLabel}
                  </span>
                )}
              </NavLink>
            )
          })}
        </nav>

        {/* Footer with User info & logout */}
        <div
          className={cn(
            'mt-auto border-t pt-3 space-y-2',
            dark ? 'border-slate-800' : 'border-slate-100',
          )}
        >
          {!collapsed ? (
            <div
              className={cn(
                'flex items-center justify-between rounded-xl p-2',
                dark ? 'bg-slate-800/60' : 'bg-slate-50',
              )}
            >
              <div className="flex items-center gap-2 min-w-0">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-700">
                  <User className="h-3.5 w-3.5" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-semibold text-slate-800">
                    {user?.full_name || user?.email || 'User'}
                  </p>
                  <p className="truncate text-[10px] uppercase tracking-wider text-slate-400">
                    {user?.role || 'Guest'}
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={handleLogout}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition"
                title="Logout"
                aria-label="Logout"
              >
                <LogOut className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : (
            <div className="flex justify-center">
              <button
                type="button"
                onClick={handleLogout}
                className="flex h-8 w-8 items-center justify-center rounded-xl text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition"
                title="Logout"
                aria-label="Logout"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      </aside>
    </>
  )
}

export default Sidebar
