import { useMemo, useState } from 'react'
import { AppShell } from '../../components/layout/AppShell'
import { PageContainer } from '../../components/layout/PageContainer'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { JobFormField } from '../../components/hiring/JobFormField'

const initialForm = {
  title: '',
  department: '',
  employmentType: 'Full-time',
  location: '',
  workMode: 'Hybrid',
  experienceLevel: 'Mid-Level',
  salaryRange: '',
  openings: '1',
  jobDescription: '',
  requiredSkills: 'React, TypeScript, UX Design',
  preferredSkills: 'Agile delivery, stakeholder communication',
  education: '',
  experienceRequirements: '',
}

const fieldOrder = [
  'title',
  'department',
  'employmentType',
  'location',
  'workMode',
  'experienceLevel',
  'salaryRange',
  'openings',
  'jobDescription',
  'requiredSkills',
  'preferredSkills',
  'education',
  'experienceRequirements',
]

const validateForm = (values) => {
  const errors = {}

  fieldOrder.forEach((field) => {
    const value = values[field]?.toString().trim()
    if (
      ['title', 'department', 'location', 'jobDescription', 'requiredSkills', 'experienceRequirements'].includes(field) &&
      !value
    ) {
      errors[field] = 'This field is required.'
    }
  })

  if (!values.salaryRange?.trim()) {
    errors.salaryRange = 'Salary range is required.'
  }

  if (!values.openings || Number(values.openings) < 1) {
    errors.openings = 'Openings must be at least 1.'
  }

  return errors
}

export function PostJobPage() {
  const [formData, setFormData] = useState(initialForm)
  const [errors, setErrors] = useState({})

  const formSummary = useMemo(() => {
    const validFields = Object.values(formData).filter((value) => String(value).trim()).length
    return `${validFields}/${fieldOrder.length} fields completed`
  }, [formData])

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormData((current) => ({ ...current, [name]: value }))

    setErrors((current) => {
      const nextErrors = { ...current }
      delete nextErrors[name]
      return nextErrors
    })
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    const nextErrors = validateForm(formData)
    setErrors(nextErrors)

    if (Object.keys(nextErrors).length > 0) {
      return
    }

    window.alert('Frontend-only validation passed. Job posting is ready for API integration.')
  }

  const handleDraft = () => {
    window.alert('Draft saved locally on the frontend. Backend integration can be added later.')
  }

  const handleCancel = () => {
    setFormData(initialForm)
    setErrors({})
  }

  return (
    <AppShell title="Hiring Dashboard">
      <PageContainer>
        <div className="flex flex-col gap-3 border-b border-slate-200 pb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Hiring</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Post a Job</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              Create a new job opening and share a clear, professional opportunity with qualified candidates.
            </p>
          </div>

          <div className="rounded-full border border-brand-100 bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">
            {formSummary}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <Card className="p-5 sm:p-6">
            <div className="mb-5">
              <h2 className="text-xl font-semibold text-slate-900">Job Information</h2>
            </div>

            <div className="grid gap-5 md:grid-cols-2">
              <JobFormField
                label="Job Title"
                id="title"
                name="title"
                value={formData.title}
                onChange={handleChange}
                placeholder="Senior Product Designer"
                error={errors.title}
              />

              <JobFormField
                label="Department"
                id="department"
                name="department"
                value={formData.department}
                onChange={handleChange}
                placeholder="Design"
                error={errors.department}
              />

              <JobFormField
                label="Employment Type"
                id="employmentType"
                name="employmentType"
                as="select"
                value={formData.employmentType}
                onChange={handleChange}
                options={[
                  { value: 'Full-time', label: 'Full-time' },
                  { value: 'Part-time', label: 'Part-time' },
                  { value: 'Contract', label: 'Contract' },
                  { value: 'Internship', label: 'Internship' },
                ]}
              />

              <JobFormField
                label="Location"
                id="location"
                name="location"
                value={formData.location}
                onChange={handleChange}
                placeholder="Bengaluru, India"
                error={errors.location}
              />

              <JobFormField
                label="Work Mode"
                id="workMode"
                name="workMode"
                as="select"
                value={formData.workMode}
                onChange={handleChange}
                options={[
                  { value: 'Hybrid', label: 'Hybrid' },
                  { value: 'Remote', label: 'Remote' },
                  { value: 'On-site', label: 'On-site' },
                ]}
              />

              <JobFormField
                label="Experience Level"
                id="experienceLevel"
                name="experienceLevel"
                as="select"
                value={formData.experienceLevel}
                onChange={handleChange}
                options={[
                  { value: 'Entry-Level', label: 'Entry-Level' },
                  { value: 'Mid-Level', label: 'Mid-Level' },
                  { value: 'Senior', label: 'Senior' },
                  { value: 'Lead', label: 'Lead' },
                ]}
              />

              <JobFormField
                label="Salary Range"
                id="salaryRange"
                name="salaryRange"
                value={formData.salaryRange}
                onChange={handleChange}
                placeholder="₹20L - ₹28L per annum"
                error={errors.salaryRange}
              />

              <JobFormField
                label="Number of Openings"
                id="openings"
                name="openings"
                type="number"
                min="1"
                value={formData.openings}
                onChange={handleChange}
                error={errors.openings}
              />
            </div>
          </Card>

          <Card className="p-5 sm:p-6">
            <div className="mb-5">
              <h2 className="text-xl font-semibold text-slate-900">Job Description</h2>
            </div>

            <JobFormField
              label="Description"
              id="jobDescription"
              name="jobDescription"
              as="textarea"
              value={formData.jobDescription}
              onChange={handleChange}
              placeholder="Describe the role, responsibilities, impact, and what success looks like..."
              error={errors.jobDescription}
            />
          </Card>

          <Card className="p-5 sm:p-6">
            <div className="mb-5">
              <h2 className="text-xl font-semibold text-slate-900">Skills & Requirements</h2>
            </div>

            <div className="grid gap-5 md:grid-cols-2">
              <JobFormField
                label="Required Skills"
                id="requiredSkills"
                name="requiredSkills"
                value={formData.requiredSkills}
                onChange={handleChange}
                placeholder="React, TypeScript, product strategy"
                error={errors.requiredSkills}
              />

              <JobFormField
                label="Preferred Skills"
                id="preferredSkills"
                name="preferredSkills"
                value={formData.preferredSkills}
                onChange={handleChange}
                placeholder="Stakeholder management, AI workflows"
              />

              <JobFormField
                label="Education"
                id="education"
                name="education"
                value={formData.education}
                onChange={handleChange}
                placeholder="B.Tech / M.Tech / relevant degree"
              />

              <JobFormField
                label="Experience Requirements"
                id="experienceRequirements"
                name="experienceRequirements"
                value={formData.experienceRequirements}
                onChange={handleChange}
                placeholder="3+ years in product or SaaS environment"
                error={errors.experienceRequirements}
              />
            </div>
          </Card>

          <Card className="border-brand-100 bg-gradient-to-br from-brand-50 to-white p-5 sm:p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">NexusAI</p>
                <h2 className="mt-2 text-xl font-semibold text-slate-900">AI Assistance</h2>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button type="button" variant="secondary" className="px-3 py-2 text-xs">
                  Generate Job Description
                </Button>
                <Button type="button" variant="secondary" className="px-3 py-2 text-xs">
                  Suggest Skills
                </Button>
                <Button type="button" variant="secondary" className="px-3 py-2 text-xs">
                  Improve Job Posting
                </Button>
              </div>
            </div>
          </Card>

          <div className="flex flex-col-reverse justify-end gap-3 border-t border-slate-200 pt-6 sm:flex-row">
            <Button type="button" variant="secondary" onClick={handleCancel}>
              Cancel
            </Button>
            <Button type="button" variant="ghost" onClick={handleDraft}>
              Save Draft
            </Button>
            <Button type="submit">Post Job</Button>
          </div>
        </form>
      </PageContainer>
    </AppShell>
  )
}
