import { Card } from '../ui/Card'

export function GovernmentStatCard({ label, value, detail }) {
  return (
    <Card className="p-5">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-3 text-3xl font-bold tracking-tight text-slate-900">{value}</p>
      <p className="mt-2 text-xs font-medium text-emerald-600">{detail}</p>
    </Card>
  )
}
