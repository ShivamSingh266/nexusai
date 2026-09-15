import { Card } from '../ui/Card'

export function StatCard({ label, value, change }) {
  return (
    <Card className="p-5">
      <p className="text-sm text-slate-500">{label}</p>
      <div className="mt-3 flex items-end justify-between gap-3">
        <p className="text-3xl font-bold tracking-tight text-slate-900">{value}</p>
      </div>
      <p className="mt-2 text-xs font-medium text-emerald-600">{change}</p>
    </Card>
  )
}
