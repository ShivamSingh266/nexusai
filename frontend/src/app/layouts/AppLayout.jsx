import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from '../../components/common/Sidebar'
import { TopNavbar } from '../../components/common/TopNavbar'
import { Breadcrumbs } from '../../components/common/Breadcrumbs'
import { ResponsiveContainer } from '../../components/common/ResponsiveContainer'
import { navigationByRole } from '../../config/navigation'

export function AppLayout() {
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('nexusai_sidebar_collapsed') === 'true')
  const [mobileOpen, setMobileOpen] = useState(false)
  const [theme, setTheme] = useState(() => localStorage.getItem('nexusai_theme') || 'light')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('nexusai_theme', theme)
  }, [theme])

  useEffect(() => {
    localStorage.setItem('nexusai_sidebar_collapsed', String(collapsed))
  }, [collapsed])

  const role = location.pathname.startsWith('/government')
    ? 'government'
    : location.pathname.startsWith('/hiring')
      ? 'recruiter'
      : 'applicant'

  const titleMap = {
    applicant: 'Applicant Portal',
    recruiter: 'Hiring Portal',
    government: 'Government Portal',
  }

  return (
    <div className={theme === 'dark' ? 'min-h-screen bg-slate-950 text-slate-100' : 'min-h-screen bg-slate-50 text-slate-900'}>
      <TopNavbar
        title={titleMap[role]}
        theme={theme}
        navigationItems={navigationByRole[role]}
        onMenuToggle={() => setMobileOpen(true)}
        onThemeToggle={() => setTheme((current) => (current === 'dark' ? 'light' : 'dark'))}
      />

      <ResponsiveContainer className="py-6">
        <div className="flex gap-6 items-start">
          <Sidebar
            items={navigationByRole[role]}
            collapsed={collapsed}
            onToggle={() => setCollapsed((current) => !current)}
            theme={theme}
            mobileOpen={mobileOpen}
            onClose={() => setMobileOpen(false)}
          />

          <main className={theme === 'dark' ? 'min-w-0 flex-1 rounded-3xl border border-slate-800 bg-slate-900 p-4 shadow-sm sm:p-6' : 'min-w-0 flex-1 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6'}>
            <div className="mb-6">
              <Breadcrumbs />
            </div>

            <Outlet />
          </main>
        </div>
      </ResponsiveContainer>
    </div>
  )
}

export default AppLayout
