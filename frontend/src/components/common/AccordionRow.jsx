import { useState } from 'react'

export function AccordionRow({ title, summary, children }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left"
      >
        <div>
          <p className="text-sm font-semibold text-slate-900">{title}</p>
          {summary && <p className="mt-1 text-xs text-slate-500">{summary}</p>}
        </div>
        <span className="text-lg text-slate-500">{expanded ? '−' : '+'}</span>
      </button>

      {expanded && <div className="border-t border-slate-200 px-4 py-3">{children}</div>}
    </div>
  )
}
