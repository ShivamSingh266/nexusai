import { cn } from '../../lib/utils'

export function Button({ children, variant = 'primary', className = '', ...props }) {
  const variants = {
    primary: 'bg-brand-600 text-white hover:bg-brand-700',
    secondary: 'bg-white text-slate-900 border border-slate-200 hover:bg-slate-50',
    ghost: 'bg-transparent text-slate-700 hover:bg-slate-100',
  }

  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-full px-5 py-2.5 text-sm font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-brand-500/30',
        variants[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}
