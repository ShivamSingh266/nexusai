import { ResponsiveContainer } from '../../components/common/ResponsiveContainer'

export function AuthLayout({ title, subtitle, children }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-brand-50/30 to-slate-100 px-4 py-12">
      <ResponsiveContainer>
        <div className="mx-auto max-w-md rounded-[28px] border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/60 sm:p-8">
          <div className="mb-8 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 to-brand-800 text-xl font-bold text-white">
              N
            </div>
            <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
            {subtitle && <p className="mt-2 text-sm text-slate-500">{subtitle}</p>}
          </div>

          {children}
        </div>
      </ResponsiveContainer>
    </div>
  )
}
