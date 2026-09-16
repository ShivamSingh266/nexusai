import { cn } from '../../lib/utils'

export function FilterBar({
  search = '',
  onSearchChange,
  filters = [],
  activeFilters = [],
  onReset,
  className = '',
}) {
  return (
    <div className={cn('rounded-2xl border border-slate-200 bg-slate-50 p-4', className)}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <input
          value={search}
          onChange={(event) => onSearchChange?.(event.target.value)}
          placeholder="Search..."
          className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none focus:border-brand-300 focus:ring-2 focus:ring-brand-100 lg:max-w-xs"
        />

        <div className="flex flex-wrap items-center gap-2">
          {filters.map((filter) => (
            <button
              key={filter.label}
              type="button"
              className={cn(
                'rounded-full border px-3 py-1.5 text-xs font-medium',
                activeFilters.includes(filter.value)
                  ? 'border-brand-200 bg-brand-50 text-brand-700'
                  : 'border-slate-200 bg-white text-slate-600',
              )}
            >
              {filter.label}
            </button>
          ))}

          <button
            type="button"
            onClick={onReset}
            className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600"
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  )
}
