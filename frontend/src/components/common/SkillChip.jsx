import { cn } from '../../lib/utils'

export function SkillChip({ skill, level, category, selected = false, variant = 'default', onClick }) {
  const variants = {
    default: 'border-slate-200 bg-slate-50 text-slate-700',
    active: 'border-brand-200 bg-brand-50 text-brand-700',
    soft: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold transition',
        selected ? variants[variant] : variants.default,
      )}
    >
      <span>{skill}</span>
      {level && <span className="rounded-full bg-white/80 px-1.5 py-0.5 text-[10px]">{level}</span>}
      {category && <span className="text-[10px] uppercase tracking-[0.12em] opacity-70">{category}</span>}
    </button>
  )
}
