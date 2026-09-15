import { Link, NavLink } from 'react-router-dom'

const navItems = [
  { label: 'Overview', to: '/hiring/dashboard' },
  { label: 'Government', to: '/government/dashboard' },
  { label: 'Skill Demand', to: '/government/skill-demand' },
  { label: 'Reports', to: '/government/reports' },
]

export function AppShell({ children, title = 'Dashboard' }) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <Link to="/" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-600 to-brand-800 text-sm font-bold text-white">
              N
            </div>
            <div>
              <div className="text-lg font-bold tracking-tight text-slate-900">NexusAI</div>
            </div>
          </Link>

          <nav className="hidden items-center gap-6 md:flex">
            {navItems.map((item) => (
              <NavLink
                key={item.label}
                to={item.to}
                className={({ isActive }) =>
                  `text-sm font-medium transition-colors ${
                    isActive ? 'text-brand-700' : 'text-slate-600 hover:text-slate-900'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <div className="mx-auto flex max-w-7xl gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <aside className="hidden w-72 shrink-0 rounded-2xl border border-slate-200 bg-white p-4 shadow-soft md:block">
          <div className="mb-6">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Workspace</p>
            <h2 className="mt-2 text-xl font-bold text-slate-900">{title}</h2>
          </div>

          <nav className="space-y-2">
            {navItems.map((item) => (
              <NavLink
                key={item.label}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-brand-50 text-brand-700 ring-1 ring-brand-200'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <main className="min-w-0 flex-1 rounded-2xl border border-slate-200 bg-white p-4 shadow-soft sm:p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
