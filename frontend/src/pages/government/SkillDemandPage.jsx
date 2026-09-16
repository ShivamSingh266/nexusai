import { useEffect, useMemo, useState } from 'react'
import { ArrowUpDown, Download, Search } from 'lucide-react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { PriorityTag } from '../../components/common/PriorityTag'
import { TrendArrow } from '../../components/common/TrendArrow'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { EmptyState } from '../../components/common/EmptyState'
import { governmentService } from '../../services/governmentService'

export function SkillDemandPage() {
  const [skills, setSkills] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [selectedSector, setSelectedSector] = useState('All')
  const [selectedRegion, setSelectedRegion] = useState('All')
  const [sortBy, setSortBy] = useState('demand') // 'demand' | 'growth' | 'name'
  const [sortOrder, setSortOrder] = useState('desc')

  useEffect(() => {
    async function loadSkills() {
      try {
        const data = await governmentService.getSkillDemand()
        setSkills(data)
      } finally {
        setLoading(false)
      }
    }
    loadSkills()
  }, [])

  const sectors = useMemo(() => {
    return ['All', ...new Set(skills.map((s) => s.sector))]
  }, [skills])

  const regions = useMemo(() => {
    return ['All', ...new Set(skills.map((s) => s.region))]
  }, [skills])

  const filteredSkills = useMemo(() => {
    return skills
      .filter((item) => {
        const matchesSearch =
          item.name.toLowerCase().includes(search.toLowerCase()) ||
          item.sector.toLowerCase().includes(search.toLowerCase()) ||
          item.region.toLowerCase().includes(search.toLowerCase())
        const matchesSector = selectedSector === 'All' || item.sector === selectedSector
        const matchesRegion = selectedRegion === 'All' || item.region === selectedRegion
        return matchesSearch && matchesSector && matchesRegion
      })
      .sort((a, b) => {
        let valA = a[sortBy]
        let valB = b[sortBy]
        if (typeof valA === 'string') {
          return sortOrder === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA)
        }
        return sortOrder === 'asc' ? valA - valB : valB - valA
      })
  }, [skills, search, selectedSector, selectedRegion, sortBy, sortOrder])

  const handleResetFilters = () => {
    setSearch('')
    setSelectedSector('All')
    setSelectedRegion('All')
    setSortBy('demand')
    setSortOrder('desc')
  }

  const toggleSort = (field) => {
    if (sortBy === field) {
      setSortOrder((curr) => (curr === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Government</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Skill Demand Intelligence</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
            Analyze skill demand intensity, growth rates, regional hotspots, and sector allocations across the national labour market.
          </p>
        </div>

        <Button variant="secondary" className="inline-flex items-center gap-2">
          <Download className="h-4 w-4" />
          <span>Export Dataset</span>
        </Button>
      </div>

      {/* Filters & Search Bar */}
      <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4 space-y-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative w-full lg:max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search skill, sector, or region..."
              className="w-full rounded-xl border border-slate-200 bg-white pl-9 pr-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Sector select */}
            <div className="flex items-center gap-1.5 text-xs font-medium text-slate-600">
              <span>Sector:</span>
              <select
                value={selectedSector}
                onChange={(e) => setSelectedSector(e.target.value)}
                className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:outline-none"
              >
                {sectors.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            {/* Region select */}
            <div className="flex items-center gap-1.5 text-xs font-medium text-slate-600">
              <span>Region:</span>
              <select
                value={selectedRegion}
                onChange={(e) => setSelectedRegion(e.target.value)}
                className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:outline-none"
              >
                {regions.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="button"
              onClick={handleResetFilters}
              className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 transition"
            >
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* Main Table / Visual Cards */}
      {loading ? (
        <div className="space-y-3">
          <LoadingSkeleton variant="table" />
          <LoadingSkeleton variant="table" />
          <LoadingSkeleton variant="table" />
          <LoadingSkeleton variant="table" />
        </div>
      ) : filteredSkills.length === 0 ? (
        <EmptyState
          title="No skills found"
          description="Try adjusting your search query or filter criteria to see available skill demand records."
          actionLabel="Clear Filters"
          onAction={handleResetFilters}
        />
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-5 py-3.5 cursor-pointer" onClick={() => toggleSort('name')}>
                    <div className="flex items-center gap-1.5">
                      <span>Skill</span>
                      <ArrowUpDown className="h-3.5 w-3.5 text-slate-400" />
                    </div>
                  </th>
                  <th className="px-5 py-3.5 cursor-pointer" onClick={() => toggleSort('demand')}>
                    <div className="flex items-center gap-1.5">
                      <span>Demand Index</span>
                      <ArrowUpDown className="h-3.5 w-3.5 text-slate-400" />
                    </div>
                  </th>
                  <th className="px-5 py-3.5 cursor-pointer" onClick={() => toggleSort('growth')}>
                    <div className="flex items-center gap-1.5">
                      <span>Growth</span>
                      <ArrowUpDown className="h-3.5 w-3.5 text-slate-400" />
                    </div>
                  </th>
                  <th className="px-5 py-3.5">Region</th>
                  <th className="px-5 py-3.5">Sector</th>
                  <th className="px-5 py-3.5">Priority</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredSkills.map((skill) => (
                  <tr key={skill.name} className="hover:bg-slate-50/80 transition">
                    <td className="px-5 py-4 font-semibold text-slate-900">{skill.name}</td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className="h-2 w-28 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-brand-600"
                            style={{ width: `${skill.demand}%` }}
                          />
                        </div>
                        <span className="font-semibold text-xs text-slate-800">{skill.demand}%</span>
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <TrendArrow direction="up" percentage={skill.growth} />
                    </td>
                    <td className="px-5 py-4">
                      <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
                        {skill.region}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-xs font-medium text-slate-600">{skill.sector}</td>
                    <td className="px-5 py-4">
                      <PriorityTag priority={skill.priority || 'medium'} />
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

export default SkillDemandPage
