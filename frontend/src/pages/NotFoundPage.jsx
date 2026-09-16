import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50 text-2xl font-bold text-brand-700">
          !
        </div>
        <h1 className="text-2xl font-bold text-slate-900">Page not found</h1>
        <p className="mt-3 text-sm text-slate-600">
          The route you requested does not exist in NexusAI.
        </p>
        <Link
          to="/"
          className="mt-6 inline-flex rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700"
        >
          Back to home
        </Link>
      </div>
    </div>
  )
}
