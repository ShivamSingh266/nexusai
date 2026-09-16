import { useEffect, useMemo, useState } from 'react'
import { BookOpen, CheckCircle2, AlertTriangle, XCircle, RefreshCw } from 'lucide-react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { AlignmentPill } from '../../components/common/AlignmentPill'
import { AccordionRow } from '../../components/common/AccordionRow'
import { ComparisonBarChart } from '../../components/charts/ComparisonBarChart'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { governmentService } from '../../services/governmentService'

export function CourseAlignmentPage() {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  useEffect(() => {
    async function loadData() {
      try {
        const data = await governmentService.getCourseAlignment()
        setCourses(data)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const filteredCourses = useMemo(() => {
    return courses.filter((c) => {
      const matchesSearch =
        c.program.toLowerCase().includes(search.toLowerCase()) ||
        c.skills.some((s) => s.toLowerCase().includes(search.toLowerCase())) ||
        c.institution.toLowerCase().includes(search.toLowerCase())
      const matchesStatus = statusFilter === 'all' || c.status === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [courses, search, statusFilter])

  // Comparison data for ComparisonBarChart
  const comparisonData = useMemo(() => {
    return courses.map((c) => ({
      label: c.program,
      demand: c.marketDemand,
      alignment: c.alignment,
    }))
  }, [courses])

  const stats = useMemo(() => {
    const total = courses.length
    const aligned = courses.filter((c) => c.status === 'aligned').length
    const partial = courses.filter((c) => c.status === 'partial').length
    const gap = courses.filter((c) => c.status === 'gap').length
    return { total, aligned, partial, gap }
  }, [courses])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Government</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Course & Training Alignment</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
            Compare public educational curricula against real-time industry skill requirements to identify training gaps and modernize programs.
          </p>
        </div>

        <Button variant="secondary" className="inline-flex items-center gap-2">
          <RefreshCw className="h-4 w-4" />
          <span>Refresh Alignment</span>
        </Button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="p-4 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500">Programs Evaluated</p>
            <p className="mt-1 text-2xl font-bold text-slate-900">{stats.total}</p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
            <BookOpen className="h-5 w-5" />
          </div>
        </Card>

        <Card className="p-4 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500">High Alignment</p>
            <p className="mt-1 text-2xl font-bold text-emerald-600">{stats.aligned}</p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700">
            <CheckCircle2 className="h-5 w-5" />
          </div>
        </Card>

        <Card className="p-4 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500">Medium Alignment</p>
            <p className="mt-1 text-2xl font-bold text-amber-600">{stats.partial}</p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50 text-amber-700">
            <AlertTriangle className="h-5 w-5" />
          </div>
        </Card>

        <Card className="p-4 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500">Low Alignment (Gap)</p>
            <p className="mt-1 text-2xl font-bold text-rose-600">{stats.gap}</p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-50 text-rose-700">
            <XCircle className="h-5 w-5" />
          </div>
        </Card>
      </div>

      {/* Comparison Bar Chart Section */}
      <Card className="p-5">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-slate-900">Curriculum Alignment vs Industry Demand</h2>
          <p className="text-xs text-slate-500">Side-by-side comparison of market demand index vs academic syllabus match</p>
        </div>
        <ComparisonBarChart
          data={comparisonData}
          series={[
            { key: 'demand', label: 'Market Demand', color: '#2563eb' },
            { key: 'alignment', label: 'Course Alignment', color: '#10b981' },
          ]}
        />
      </Card>

      {/* Filter and Search Bar */}
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by course or skill..."
          className="w-full sm:max-w-xs rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
        />

        <div className="flex flex-wrap items-center gap-2">
          {[
            { label: 'All Courses', value: 'all' },
            { label: 'High Alignment', value: 'aligned' },
            { label: 'Medium Alignment', value: 'partial' },
            { label: 'Low Alignment', value: 'gap' },
          ].map((pill) => (
            <button
              key={pill.value}
              type="button"
              onClick={() => setStatusFilter(pill.value)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                statusFilter === pill.value
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
              }`}
            >
              {pill.label}
            </button>
          ))}
        </div>
      </div>

      {/* Accordion Rows for detailed course breakdowns */}
      <div className="space-y-3">
        {loading ? (
          <div className="space-y-3">
            <LoadingSkeleton variant="card" />
            <LoadingSkeleton variant="card" />
          </div>
        ) : (
          filteredCourses.map((course) => (
            <AccordionRow
              key={course.program}
              title={
                <div className="flex flex-wrap items-center gap-3">
                  <span className="text-base font-bold text-slate-900">{course.program}</span>
                  <AlignmentPill
                    status={course.status}
                    score={course.alignment}
                    tooltip={`Alignment: ${course.alignmentLevel}`}
                  />
                  <span className="text-xs text-slate-400">({course.institution})</span>
                </div>
              }
              summary={course.summary}
            >
              <div className="pt-2 space-y-4">
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Skills Covered</p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {course.skills.map((s) => (
                        <span key={s} className="rounded-md bg-white border border-slate-200 px-2 py-0.5 text-xs text-slate-700">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Duration & Institution</p>
                    <p className="mt-1.5 text-sm font-semibold text-slate-800">{course.duration}</p>
                    <p className="text-xs text-slate-500">{course.institution}</p>
                  </div>

                  <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Alignment Score Breakdown</p>
                    <div className="mt-1.5 space-y-1 text-xs">
                      <div className="flex justify-between text-slate-600">
                        <span>Market Demand:</span>
                        <span className="font-semibold text-slate-800">{course.marketDemand}%</span>
                      </div>
                      <div className="flex justify-between text-slate-600">
                        <span>Curriculum Score:</span>
                        <span className="font-semibold text-slate-800">{course.curriculumScore}%</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="rounded-xl border border-amber-200 bg-amber-50/60 p-3.5">
                  <p className="text-xs font-semibold text-amber-900 uppercase tracking-wider">Policy & Curriculum Action Plan</p>
                  <p className="mt-1 text-sm text-amber-800 leading-relaxed">{course.gap}</p>
                </div>
              </div>
            </AccordionRow>
          ))
        )}
      </div>
    </div>
  )
}

export default CourseAlignmentPage
