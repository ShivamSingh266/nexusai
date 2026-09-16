import { useEffect, useMemo, useRef, useState } from 'react'
import { Search, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { cn } from '../../lib/utils'

export function SearchCommand({ items = [], theme = 'light' }) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const inputRef = useRef(null)
  const navigate = useNavigate()

  const results = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()

    if (!normalizedQuery) {
      return items
    }

    return items.filter((item) => (item.title || item.label).toLowerCase().includes(normalizedQuery))
  }, [items, query])

  useEffect(() => {
    const handleShortcut = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setOpen(true)
      }

      if (event.key === 'Escape') {
        setOpen(false)
      }
    }

    document.addEventListener('keydown', handleShortcut)
    return () => document.removeEventListener('keydown', handleShortcut)
  }, [])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  const goToItem = (path) => {
    setOpen(false)
    navigate(path)
  }

  return (
    <>
      <button
        type="button"
        onClick={() => {
          setQuery('')
          setOpen(true)
        }}
        className={cn(
          'flex w-full max-w-xl items-center justify-between rounded-2xl border px-4 py-2.5 text-left text-sm transition',
          theme === 'dark'
            ? 'border-slate-700 bg-slate-900 text-slate-300 hover:border-brand-400'
            : 'border-slate-200 bg-slate-50 text-slate-500 hover:border-brand-300 hover:bg-white',
        )}
        aria-label="Open navigation search"
      >
        <span className="flex items-center gap-3">
          <Search className="h-4 w-4" />
          <span>Search pages...</span>
        </span>
        <kbd className={cn('hidden rounded-md border px-2 py-0.5 text-[11px] font-medium sm:inline', theme === 'dark' ? 'border-slate-700 text-slate-400' : 'border-slate-200 text-slate-400')}>
          Ctrl K
        </kbd>
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-slate-950/40 px-4 pt-[12vh]" onMouseDown={() => setOpen(false)}>
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Search navigation"
            className={cn('w-full max-w-xl overflow-hidden rounded-2xl border shadow-2xl', theme === 'dark' ? 'border-slate-700 bg-slate-900' : 'border-slate-200 bg-white')}
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className={cn('flex items-center gap-3 border-b px-4', theme === 'dark' ? 'border-slate-700' : 'border-slate-200')}>
              <Search className="h-4 w-4 text-slate-400" />
              <input
                ref={inputRef}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Escape') setOpen(false)
                  if (event.key === 'Enter' && results[0]) goToItem(results[0].path)
                }}
                placeholder="Search this workspace"
                className={cn('min-w-0 flex-1 bg-transparent py-4 text-sm outline-none', theme === 'dark' ? 'text-slate-100 placeholder:text-slate-500' : 'text-slate-900 placeholder:text-slate-400')}
              />
              <button type="button" onClick={() => setOpen(false)} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700" aria-label="Close search">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="max-h-72 overflow-y-auto p-2">
              {results.length === 0 ? (
                <p className="px-3 py-8 text-center text-sm text-slate-500">No matching pages found.</p>
              ) : (
                results.map((item) => {
                  const Icon = item.icon
                  return (
                    <button
                      key={item.id || item.path}
                      type="button"
                      onClick={() => goToItem(item.path)}
                      className={cn('flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm transition', theme === 'dark' ? 'text-slate-200 hover:bg-slate-800' : 'text-slate-700 hover:bg-slate-50')}
                    >
                      <span className={cn('flex h-8 w-8 items-center justify-center rounded-lg', theme === 'dark' ? 'bg-slate-800 text-slate-300' : 'bg-slate-100 text-slate-600')}>
                        {Icon ? <Icon className="h-4 w-4" /> : <Search className="h-4 w-4" />}
                      </span>
                      <span>{item.title || item.label}</span>
                    </button>
                  )
                })
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
