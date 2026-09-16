import { useMemo, useState } from 'react'
import { AppShell } from '../../components/layout/AppShell'
import { PageContainer } from '../../components/layout/PageContainer'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { JobFormField } from '../../components/hiring/JobFormField'
import { useAuth } from '../../auth/AuthContext'
import {
  createJob,
  createJobSkills,
  getVersions,
  searchTaxonomy,
} from '../../services/recruiter'

const initialForm = {
  title: '',
  department: '',
  employmentType: 'full_time',
  location: '',
  workMode: 'hybrid',
  experienceLevel: 'mid',
  salaryRange: '',
  openings: '1',
  jobDescription: '',
  preferredSkills: '',
  education: '',
  experienceRequirements: '',
}

const experienceRanges = {
  entry: [0, 2],
  mid: [2, 5],
  senior: [5, 10],
  lead: [8, null],
}

const buildJobPayload = (formData, status) => {
  const [experienceMin, experienceMax] = experienceRanges[formData.experienceLevel]
  return {
    title: formData.title.trim(),
    description: formData.jobDescription.trim() || null,
    location: formData.location.trim() || null,
    employment_type: formData.employmentType || null,
    work_mode: formData.workMode || null,
    experience_min: experienceMin,
    experience_max: experienceMax,
    education_requirement: formData.education.trim() || null,
    status,
  }
}

export function PostJobPage() {
  const { accessToken } = useAuth()
  const [formData, setFormData] = useState(initialForm)
  const [selectedSkills, setSelectedSkills] = useState([])
  const [skillQuery, setSkillQuery] = useState('')
  const [skillResults, setSkillResults] = useState([])
  const [errors, setErrors] = useState({})
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [searching, setSearching] = useState(false)
  const [createdJobId, setCreatedJobId] = useState(null)
  const [pendingSkills, setPendingSkills] = useState([])
  const [retryingSkills, setRetryingSkills] = useState(false)

  const formSummary = useMemo(() => {
    const filled = Object.values(formData).filter((value) => String(value).trim()).length
    return `${filled}/${Object.keys(formData).length} fields completed`
  }, [formData])

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormData((current) => ({ ...current, [name]: value }))
    setErrors((current) => ({ ...current, [name]: '' }))
  }

  const searchSkills = async () => {
    if (!skillQuery.trim()) return
    setSearching(true)
    setError('')
    try {
      const response = await searchTaxonomy(skillQuery.trim(), accessToken)
      setSkillResults(response.results)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setSearching(false)
    }
  }

  const selectSkill = (skill) => {
    if (!selectedSkills.some((item) => item.skill_id === skill.skill_id)) {
      setSelectedSkills((current) => [...current, skill])
    }
    setSkillQuery('')
    setSkillResults([])
  }

  const validateForm = () => {
    const nextErrors = {}
    if (!formData.title.trim()) nextErrors.title = 'Job title is required.'
    if (!formData.location.trim()) nextErrors.location = 'Location is required.'
    if (!formData.jobDescription.trim()) nextErrors.jobDescription = 'Description is required.'
    if (selectedSkills.length === 0) nextErrors.requiredSkills = 'Select at least one canonical skill.'
    setErrors(nextErrors)
    return Object.keys(nextErrors).length === 0
  }

  const submitJob = async (status) => {
    if (submitting || createdJobId || !validateForm()) return
    setSubmitting(true)
    setError('')
    setNotice('')
    try {
      const versionsResponse = await getVersions(accessToken)
      const taxonomyVersion = versionsResponse.data.taxonomy_version
      const skills = selectedSkills.map((skill) => ({
        skill_id: skill.skill_id,
        taxonomy_version: taxonomyVersion,
        role_importance: 1,
        is_mandatory: true,
      }))
      const jobResponse = await createJob(buildJobPayload(formData, status), accessToken)
      setCreatedJobId(jobResponse.id)
      setPendingSkills(skills)
      try {
        await createJobSkills(jobResponse.id, skills, accessToken)
      } catch (skillError) {
        setError(`Job #${jobResponse.id} was created, but its skills were not saved. ${skillError.message}`)
        return
      }
      setNotice(status === 'published' ? 'Job posted successfully.' : 'Draft saved successfully.')
      setFormData(initialForm)
      setSelectedSkills([])
      setCreatedJobId(null)
      setPendingSkills([])
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setSubmitting(false)
    }
  }

  const retrySkills = async () => {
    if (!createdJobId || retryingSkills) return
    setRetryingSkills(true)
    setError('')
    try {
      await createJobSkills(createdJobId, pendingSkills, accessToken)
      setNotice(`Skills saved successfully for job #${createdJobId}.`)
      setFormData(initialForm)
      setSelectedSkills([])
      setCreatedJobId(null)
      setPendingSkills([])
    } catch (requestError) {
      setError(`Job #${createdJobId} was created, but its skills were not saved. ${requestError.message}`)
    } finally {
      setRetryingSkills(false)
    }
  }

  return (
    <AppShell title="Hiring Dashboard">
      <PageContainer>
        <div className="flex flex-col gap-3 border-b border-slate-200 pb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Hiring</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Post a Job</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">Create a new job opening for your company.</p>
          </div>
          <div className="rounded-full border border-brand-100 bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">{formSummary}</div>
        </div>

        {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {notice ? <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{notice}</p> : null}
        {createdJobId ? (
          <Card className="border-amber-200 bg-amber-50 p-5">
            <p className="text-sm font-semibold text-amber-900">Job #{createdJobId} was created, but its skills still need to be saved.</p>
            <Button type="button" className="mt-3" onClick={retrySkills} disabled={retryingSkills}>{retryingSkills ? 'Saving skills...' : 'Retry saving skills'}</Button>
          </Card>
        ) : null}

        <form onSubmit={(event) => { event.preventDefault(); submitJob('published') }} className="space-y-6">
          <Card className="p-5 sm:p-6">
            <h2 className="mb-5 text-xl font-semibold text-slate-900">Job Information</h2>
            <div className="grid gap-5 md:grid-cols-2">
              <JobFormField label="Job Title" id="title" name="title" value={formData.title} onChange={handleChange} placeholder="Senior Product Designer" error={errors.title} />
              <JobFormField label="Department" id="department" name="department" value={formData.department} onChange={handleChange} placeholder="Design" />
              <JobFormField label="Employment Type" id="employmentType" name="employmentType" as="select" value={formData.employmentType} onChange={handleChange} options={[
                { value: 'full_time', label: 'Full-time' }, { value: 'part_time', label: 'Part-time' }, { value: 'contract', label: 'Contract' }, { value: 'internship', label: 'Internship' }, { value: 'freelance', label: 'Freelance' },
              ]} />
              <JobFormField label="Location" id="location" name="location" value={formData.location} onChange={handleChange} placeholder="Bengaluru, India" error={errors.location} />
              <JobFormField label="Work Mode" id="workMode" name="workMode" as="select" value={formData.workMode} onChange={handleChange} options={[
                { value: 'hybrid', label: 'Hybrid' }, { value: 'remote', label: 'Remote' }, { value: 'onsite', label: 'On-site' },
              ]} />
              <JobFormField label="Experience Level" id="experienceLevel" name="experienceLevel" as="select" value={formData.experienceLevel} onChange={handleChange} options={[
                { value: 'entry', label: 'Entry-Level' }, { value: 'mid', label: 'Mid-Level' }, { value: 'senior', label: 'Senior' }, { value: 'lead', label: 'Lead' },
              ]} />
              <JobFormField label="Salary Range" id="salaryRange" name="salaryRange" value={formData.salaryRange} onChange={handleChange} placeholder="₹20L - ₹28L per annum" />
              <JobFormField label="Number of Openings" id="openings" name="openings" type="number" min="1" value={formData.openings} onChange={handleChange} />
            </div>
          </Card>

          <Card className="p-5 sm:p-6">
            <h2 className="mb-5 text-xl font-semibold text-slate-900">Job Description</h2>
            <JobFormField label="Description" id="jobDescription" name="jobDescription" as="textarea" value={formData.jobDescription} onChange={handleChange} placeholder="Describe the role and responsibilities..." error={errors.jobDescription} />
          </Card>

          <Card className="p-5 sm:p-6">
            <h2 className="mb-5 text-xl font-semibold text-slate-900">Skills & Requirements</h2>
            <div className="grid gap-5 md:grid-cols-2">
              <div>
                <label htmlFor="skillQuery" className="block text-sm font-medium text-slate-700">Required canonical skills</label>
                <div className="mt-2 flex gap-2">
                  <input id="skillQuery" value={skillQuery} onChange={(event) => setSkillQuery(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') { event.preventDefault(); searchSkills() } }} placeholder="Search taxonomy skills" className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm" />
                  <Button type="button" variant="secondary" onClick={searchSkills} disabled={searching}>{searching ? '...' : 'Search'}</Button>
                </div>
                {errors.requiredSkills ? <span className="mt-1 inline-block text-xs text-red-600">{errors.requiredSkills}</span> : null}
                {skillResults.length > 0 ? <div className="mt-2 space-y-1 rounded-xl border border-slate-200 bg-white p-2">{skillResults.map((skill) => <button type="button" key={skill.skill_id} onClick={() => selectSkill(skill)} className="block w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-brand-50">{skill.canonical_name} <span className="text-xs text-slate-500">{skill.skill_id}</span></button>)}</div> : null}
                <div className="mt-3 flex flex-wrap gap-2">{selectedSkills.map((skill) => <span key={skill.skill_id} className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">{skill.canonical_name} <button type="button" onClick={() => setSelectedSkills((current) => current.filter((item) => item.skill_id !== skill.skill_id))} aria-label={`Remove ${skill.canonical_name}`}>×</button></span>)}</div>
              </div>
              <JobFormField label="Preferred Skills" id="preferredSkills" name="preferredSkills" value={formData.preferredSkills} onChange={handleChange} placeholder="Stakeholder management, AI workflows" />
              <JobFormField label="Education" id="education" name="education" value={formData.education} onChange={handleChange} placeholder="Relevant degree" />
              <JobFormField label="Experience Requirements" id="experienceRequirements" name="experienceRequirements" value={formData.experienceRequirements} onChange={handleChange} placeholder="Additional experience details" />
            </div>
          </Card>

          <div className="flex flex-col-reverse justify-end gap-3 border-t border-slate-200 pt-6 sm:flex-row">
            <Button type="button" variant="secondary" onClick={() => { setFormData(initialForm); setSelectedSkills([]); setErrors({}); setError(''); }}>Cancel</Button>
            <Button type="button" variant="ghost" onClick={() => submitJob('draft')} disabled={submitting || Boolean(createdJobId)}>Save Draft</Button>
            <Button type="submit" disabled={submitting || Boolean(createdJobId)}>{submitting ? 'Saving...' : 'Post Job'}</Button>
          </div>
        </form>
      </PageContainer>
    </AppShell>
  )
}
