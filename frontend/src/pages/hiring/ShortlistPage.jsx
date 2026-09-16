import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FolderKanban, Users, CheckCircle2, Clock, XCircle, ArrowRight } from 'lucide-react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { StatCard } from '../../components/common/StatCard'
import { MatchScoreBadge } from '../../components/common/MatchScoreBadge'
import { Toast } from '../../components/common/Toast'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { EmptyState } from '../../components/common/EmptyState'
import { hiringService } from '../../services/hiringService'

const STAGES = ['All', 'New', 'Reviewed', 'Interview', 'Selected', 'Rejected']

const stageBadgeStyles = {
  New: 'bg-indigo-100 text-indigo-800 border-indigo-200',
  Reviewed: 'bg-amber-100 text-amber-800 border-amber-200',
  Interview: 'bg-blue-100 text-blue-800 border-blue-200',
  Selected: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  Rejected: 'bg-rose-100 text-rose-800 border-rose-200',
}

export function ShortlistPage() {
  const navigate = useNavigate()
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedStage, setSelectedStage] = useState('All')
  const [search, setSearch] = useState('')
  const [toast, setToast] = useState(null)

  useEffect(() => {
    async function loadShortlist() {
      try {
        const data = await hiringService.getShortlist()
        // Map any legacy stage names to standard states
        const normalized = data.map((c) => ({
          ...c,
          stage: c.stage === 'Shortlisted' ? 'New' : c.stage === 'Review' ? 'Reviewed' : c.stage,
        }))
        setCandidates(normalized)
      } finally {
        setLoading(false)
      }
    }
    loadShortlist()
  }, [])

  const filteredCandidates = useMemo(() => {
    return candidates.filter((c) => {
      const matchesStage = selectedStage === 'All' || c.stage === selectedStage
      const matchesSearch =
        c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.role.toLowerCase().includes(search.toLowerCase()) ||
        c.skills.some((s) => s.toLowerCase().includes(search.toLowerCase()))
      return matchesStage && matchesSearch
    })
  }, [candidates, selectedStage, search])

  const stats = useMemo(() => {
    const total = candidates.length
    const inInterview = candidates.filter((c) => c.stage === 'Interview').length
    const selected = candidates.filter((c) => c.stage === 'Selected').length
    const reviewed = candidates.filter((c) => c.stage === 'Reviewed' || c.stage === 'New').length
    return { total, inInterview, selected, reviewed }
  }, [candidates])

  const handleStageChange = (candidateId, nextStage) => {
    setCandidates((prev) =>
      prev.map((c) => (c.id === candidateId ? { ...c, stage: nextStage } : c)),
    )
    const cand = candidates.find((c) => c.id === candidateId)
    setToast({
      variant: 'success',
      title: 'Status Updated',
      message: `${cand?.name || 'Candidate'} moved to "${nextStage}".`,
    })
  }

  return (
    <div className="space-y-6">
      {toast && (
        <div className="fixed bottom-6 right-6 z-50">
          <Toast
            variant={toast.variant}
            title={toast.title}
            message={toast.message}
            duration={3500}
            onDismiss={() => setToast(null)}
          />
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Hiring</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Shortlisted Candidates</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
            Manage your recruitment funnel stages: review qualified profiles, advance candidates to interview, and track offers.
          </p>
        </div>

        <Button
          onClick={() => navigate('/hiring/candidate-matching')}
          className="inline-flex items-center gap-2"
        >
          <span>Match More Candidates</span>
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Total Shortlisted"
          value={stats.total}
          subtitle="Active pipeline"
          icon={<FolderKanban className="h-5 w-5 text-brand-600" />}
        />
        <StatCard
          title="Under Review"
          value={stats.reviewed}
          subtitle="New & reviewed profiles"
          icon={<Clock className="h-5 w-5 text-amber-600" />}
        />
        <StatCard
          title="In Interview"
          value={stats.inInterview}
          subtitle="Scheduled rounds"
          icon={<Users className="h-5 w-5 text-blue-600" />}
        />
        <StatCard
          title="Selected / Offer"
          value={stats.selected}
          subtitle="Offer stage finalists"
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-600" />}
        />
      </div>

      {/* Stage Tabs & Search Filter */}
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter by name, role, or skill..."
          className="w-full sm:max-w-xs rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
        />

        <div className="flex flex-wrap items-center gap-1.5">
          {STAGES.map((stg) => (
            <button
              key={stg}
              type="button"
              onClick={() => setSelectedStage(stg)}
              className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                selectedStage === stg
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
              }`}
            >
              {stg}
            </button>
          ))}
        </div>
      </div>

      {/* Candidate Pipeline Table */}
      {loading ? (
        <div className="space-y-3">
          <LoadingSkeleton variant="table" />
          <LoadingSkeleton variant="table" />
          <LoadingSkeleton variant="table" />
        </div>
      ) : filteredCandidates.length === 0 ? (
        <EmptyState
          title="No candidates in this stage"
          description="Adjust your stage filter or search term to view other candidate records."
          actionLabel="View All Stages"
          onAction={() => {
            setSelectedStage('All')
            setSearch('')
          }}
        />
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-5 py-3.5">Candidate</th>
                  <th className="px-5 py-3.5">Target Role</th>
                  <th className="px-5 py-3.5">Match Score</th>
                  <th className="px-5 py-3.5">Stage</th>
                  <th className="px-5 py-3.5 text-right">Stage Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredCandidates.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/80 transition">
                    <td className="px-5 py-4">
                      <div>
                        <p className="font-bold text-slate-900">{c.name}</p>
                        <p className="text-xs text-slate-500 mt-0.5">{c.experience} exp • {c.education}</p>
                      </div>
                    </td>

                    <td className="px-5 py-4 text-xs font-medium text-slate-700">{c.role}</td>

                    <td className="px-5 py-4">
                      <MatchScoreBadge score={c.matchScore} />
                    </td>

                    <td className="px-5 py-4">
                      <span
                        className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
                          stageBadgeStyles[c.stage] || 'bg-slate-100 text-slate-700 border-slate-200'
                        }`}
                      >
                        {c.stage}
                      </span>
                    </td>

                    <td className="px-5 py-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <select
                          value={c.stage}
                          onChange={(e) => handleStageChange(c.id, e.target.value)}
                          className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-400"
                        >
                          <option value="New">New</option>
                          <option value="Reviewed">Reviewed</option>
                          <option value="Interview">Interview</option>
                          <option value="Selected">Selected</option>
                          <option value="Rejected">Rejected</option>
                        </select>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}

export default ShortlistPage
