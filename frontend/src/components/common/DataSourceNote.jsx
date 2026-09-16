export function DataSourceNote({ model_version, source_version, generated_at, warnings = [] }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
      <div className="flex flex-wrap items-center gap-3">
        <span className="font-medium text-slate-700">Model:</span>
        <span>{model_version || 'N/A'}</span>
        <span className="text-slate-300">•</span>
        <span className="font-medium text-slate-700">Source:</span>
        <span>{source_version || 'N/A'}</span>
      </div>

      <div className="mt-2 text-xs text-slate-500">
        Generated at: {generated_at || 'Not available'}
      </div>

      {warnings.length > 0 && (
        <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-amber-700">
          {warnings.map((warning, index) => (
            <li key={`${warning}-${index}`}>{warning}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
