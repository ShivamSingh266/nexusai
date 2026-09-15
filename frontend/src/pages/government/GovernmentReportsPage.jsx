import { AppShell } from '../../components/layout/AppShell'
import { PageContainer } from '../../components/layout/PageContainer'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { governmentReports } from '../../mocks/governmentMockData'

export function GovernmentReportsPage() {
  return (
    <AppShell title="Government Dashboard">
      <PageContainer>
        <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Government</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Government Reports</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              View available reports, monitor status, and prepare for deeper analysis and future export workflows.
            </p>
          </div>
          <Button variant="secondary">New report</Button>
        </div>

        <Card className="p-5">
          <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Available reports</h2>
            <input
              type="text"
              placeholder="Search reports"
              className="w-full max-w-xs rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
            />
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">Report</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {governmentReports.map((report) => (
                  <tr key={report.title} className="border-t border-slate-200">
                    <td className="px-4 py-4 font-medium text-slate-900">{report.title}</td>
                    <td className="px-4 py-4">{report.type}</td>
                    <td className="px-4 py-4">{report.date}</td>
                    <td className="px-4 py-4">
                      <span className="inline-flex rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                        {report.status}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <button type="button" className="font-medium text-brand-700 hover:text-brand-800">
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </PageContainer>
    </AppShell>
  )
}
