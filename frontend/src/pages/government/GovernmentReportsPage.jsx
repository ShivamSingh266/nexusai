import { useEffect, useMemo, useState } from 'react'
import { FileText, Download, Calendar, Search, CheckCircle2, Clock } from 'lucide-react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { Toast } from '../../components/common/Toast'
import { governmentService } from '../../services/governmentService'

export function GovernmentReportsPage() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [toastMessage, setToastMessage] = useState('')

  useEffect(() => {
    async function loadReports() {
      try {
        const data = await governmentService.getReports()
        setReports(data)
      } finally {
        setLoading(false)
      }
    }
    loadReports()
  }, [])

  const filteredReports = useMemo(() => {
    return reports.filter(
      (r) =>
        r.title.toLowerCase().includes(search.toLowerCase()) ||
        r.description.toLowerCase().includes(search.toLowerCase()) ||
        r.type.toLowerCase().includes(search.toLowerCase()),
    )
  }, [reports, search])

  const handleDownload = (reportTitle) => {
    setToastMessage(`Downloading latest export for "${reportTitle}"...`)
  }

  return (
    <div className="space-y-6">
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50">
          <Toast
            variant="success"
            title="Report Export"
            message={toastMessage}
            duration={3500}
            onDismiss={() => setToastMessage('')}
          />
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Government</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Government Intelligence Reports</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
            Access statutory workforce assessments, curriculum alignment reviews, regional forecasts, and policy evaluation documents.
          </p>
        </div>

        <Button
          variant="secondary"
          onClick={() => setToastMessage('Generating ad-hoc intelligence brief...')}
          className="inline-flex items-center gap-2"
        >
          <FileText className="h-4 w-4" />
          <span>New Custom Report</span>
        </Button>
      </div>

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter reports by title, keyword, or domain..."
          className="w-full rounded-xl border border-slate-200 bg-white pl-9 pr-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
        />
      </div>

      {/* Report Cards Grid */}
      {loading ? (
        <div className="grid gap-4 md:grid-cols-2">
          <LoadingSkeleton variant="card" />
          <LoadingSkeleton variant="card" />
          <LoadingSkeleton variant="card" />
          <LoadingSkeleton variant="card" />
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2">
          {filteredReports.map((report) => (
            <Card key={report.id || report.title} className="p-5 flex flex-col justify-between hover:shadow-md transition">
              <div>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div>
                      <h2 className="text-base font-bold text-slate-900">{report.title}</h2>
                      <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">{report.type}</span>
                    </div>
                  </div>

                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                      report.status === 'Ready'
                        ? 'bg-emerald-100 text-emerald-800'
                        : report.status === 'Reviewed'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {report.status === 'Ready' ? (
                      <CheckCircle2 className="h-3 w-3" />
                    ) : (
                      <Clock className="h-3 w-3" />
                    )}
                    {report.status}
                  </span>
                </div>

                <p className="mt-3 text-xs leading-relaxed text-slate-600">{report.description}</p>

                <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-slate-500 pt-3 border-t border-slate-100">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5 text-slate-400" />
                    <span>{report.date}</span>
                  </div>

                  <div className="rounded-md bg-slate-100 px-2 py-0.5 font-semibold text-slate-700">
                    {report.metric}
                  </div>
                </div>
              </div>

              <div className="mt-5 flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => handleDownload(report.title)}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition"
                >
                  <Download className="h-3.5 w-3.5" />
                  <span>Download PDF</span>
                </button>

                <button
                  type="button"
                  onClick={() => setToastMessage(`Viewing detailed analytics for ${report.title}`)}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-brand-700 transition"
                >
                  <span>View Details</span>
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

export default GovernmentReportsPage
