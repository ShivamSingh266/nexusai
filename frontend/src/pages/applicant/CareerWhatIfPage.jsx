export function CareerWhatIfPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Career what-if</p>
        <h2 className="mt-2 text-3xl font-bold text-slate-900">Explore alternate career paths</h2>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {[
          { title: 'Product Analyst', score: '89%' },
          { title: 'Business Intelligence Lead', score: '84%' },
          { title: 'AI Product Specialist', score: '81%' },
        ].map((option) => (
          <div key={option.title} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900">{option.title}</h3>
            <p className="mt-4 text-3xl font-bold text-brand-700">{option.score}</p>
            <p className="mt-2 text-sm text-slate-500">Estimated fit</p>
          </div>
        ))}
      </div>
    </div>
  )
}
