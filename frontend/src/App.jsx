import { Link, Navigate } from 'react-router-dom'
import { auth, getDefaultDashboardForRole } from './services/auth'

function App() {
  const user = auth.getUser()

  if (auth.isAuthenticated() && user) {
    return <Navigate to={getDefaultDashboardForRole(user.role)} replace />
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-5 sm:px-6 lg:px-8">
          <Link to="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-600 to-brand-800 font-bold text-white">
              N
            </div>

            <div>
              <div className="text-xl font-bold tracking-tight">NexusAI</div>
              <div className="text-xs text-slate-500">Labour Market Intelligence</div>
            </div>
          </Link>

          <div className="flex items-center gap-3">
            <Link to="/login" className="rounded-xl px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900">
              Login
            </Link>
            <Link to="/register" className="rounded-xl px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900">
              Register
            </Link>
            <Link to="/applicant/dashboard" className="rounded-xl px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900">
              Applicant
            </Link>
            <Link to="/hiring/dashboard" className="rounded-xl px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900">
              Hiring
            </Link>
            <Link to="/government/dashboard" className="rounded-xl px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900">
              Government
            </Link>
          </div>
        </div>
      </header>

      <main>
        <section className="mx-auto max-w-7xl px-4 pb-20 pt-20 sm:px-6 lg:px-8 lg:pb-28 lg:pt-28">
          <div className="mx-auto max-w-4xl text-center">
            <div className="mb-6 inline-flex rounded-full border border-brand-200 bg-brand-50 px-4 py-2 text-sm font-medium text-brand-700">
              AI-powered labour market intelligence
            </div>

            <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
              Connecting talent,
              <span className="block text-brand-700">skills and opportunities.</span>
            </h1>

            <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              NexusAI helps organizations understand talent demand, identify relevant skills and make better workforce decisions using intelligent labour-market insights.
            </p>

            <div className="mt-10 flex flex-col justify-center gap-4 sm:flex-row">
              <Link to="/applicant/dashboard" className="rounded-xl bg-brand-700 px-6 py-3.5 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-800">
                Explore Applicant
              </Link>
              <Link to="/hiring/dashboard" className="rounded-xl border border-slate-300 bg-white px-6 py-3.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-100">
                Explore Hiring
              </Link>
              <Link to="/government/dashboard" className="rounded-xl border border-slate-300 bg-white px-6 py-3.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-100">
                Explore Government
              </Link>
            </div>
          </div>
        </section>

        <section className="border-y border-slate-200 bg-white">
          <div className="mx-auto grid max-w-7xl gap-6 px-4 py-12 sm:px-6 md:grid-cols-3 lg:px-8">
            <div className="rounded-2xl border border-slate-200 p-6 shadow-sm">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 font-bold text-brand-700">A</div>
              <h2 className="text-lg font-bold">Applicant</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">Track readiness, discover roles, and navigate your career roadmap with AI-guided insights.</p>
            </div>

            <div className="rounded-2xl border border-slate-200 p-6 shadow-sm">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 font-bold text-brand-700">H</div>
              <h2 className="text-lg font-bold">Hiring</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">Support recruiters with job management, candidate matching and shortlist workflows.</p>
            </div>

            <div className="rounded-2xl border border-slate-200 p-6 shadow-sm">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 font-bold text-brand-700">G</div>
              <h2 className="text-lg font-bold">Government</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">Provide workforce intelligence and recommendations to support evidence-based planning.</p>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-slate-50">
        <div className="mx-auto max-w-7xl px-4 py-8 text-center text-sm text-slate-500 sm:px-6 lg:px-8">
          NexusAI — Labour Market Intelligence Platform
        </div>
      </footer>
    </div>
  )
}

export default App