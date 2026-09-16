import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Briefcase, Building, MapPin, DollarSign, GraduationCap, CheckCircle2, ArrowLeft } from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Toast } from '../../components/common/Toast'
import { hiringService } from '../../services/hiringService'

const initialForm = {
  title: '',
  company: 'NexusAI Global Labs',
  location: '',
  employmentType: 'Full-time',
  salary: '',
  requiredSkills: '',
  experience: '',
  education: 'Bachelor’s Degree in Computer Science or related field',
  jobDescription: '',
}

export function PostJobPage() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState(initialForm)
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null) // { variant, title, message }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    if (errors[name]) {
      setErrors((prev) => {
        const copy = { ...prev }
        delete copy[name]
        return copy
      })
    }
  }

  const validate = () => {
    const nextErrors = {}
    if (!formData.title.trim()) nextErrors.title = 'Job title is required.'
    if (!formData.company.trim()) nextErrors.company = 'Company name is required.'
    if (!formData.location.trim()) nextErrors.location = 'Location is required.'
    if (!formData.salary.trim()) nextErrors.salary = 'Salary range is required.'
    if (!formData.requiredSkills.trim()) nextErrors.requiredSkills = 'At least one required skill is needed.'
    if (!formData.experience.trim()) nextErrors.experience = 'Experience level is required.'
    if (!formData.jobDescription.trim()) nextErrors.jobDescription = 'Job description is required.'
    return nextErrors
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const validationErrors = validate()
    setErrors(validationErrors)

    if (Object.keys(validationErrors).length > 0) {
      setToast({
        variant: 'error',
        title: 'Validation Error',
        message: 'Please resolve the highlighted fields before submitting.',
      })
      return
    }

    setLoading(true)
    try {
      await hiringService.createJob({
        title: formData.title,
        company: formData.company,
        location: formData.location,
        employment_type: formData.employmentType,
        salary_range: formData.salary,
        required_skills: formData.requiredSkills.split(',').map((s) => s.trim()),
        experience: formData.experience,
        education: formData.education,
        description: formData.jobDescription,
      })

      setToast({
        variant: 'success',
        title: 'Job Posted Successfully',
        message: `"${formData.title}" has been published and is now matching candidates.`,
      })

      // Reset form after short delay and navigate
      setTimeout(() => {
        navigate('/hiring/dashboard')
      }, 1500)
    } catch {
      setToast({
        variant: 'error',
        title: 'Posting Failed',
        message: 'Unable to submit job posting. Please try again.',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {toast && (
        <div className="fixed bottom-6 right-6 z-50">
          <Toast
            variant={toast.variant}
            title={toast.title}
            message={toast.message}
            duration={4000}
            onDismiss={() => setToast(null)}
          />
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col gap-3 border-b border-slate-200 pb-6 md:flex-row md:items-center md:justify-between">
        <div>
          <button
            type="button"
            onClick={() => navigate('/hiring/dashboard')}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition mb-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Dashboard
          </button>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Post a New Job Opportunity</h1>
          <p className="mt-1 text-sm text-slate-600">
            Define requirements, competencies, and compensation to immediately trigger AI candidate matching.
          </p>
        </div>
      </div>

      <Card className="p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Row 1: Title & Company */}
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label htmlFor="title" className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                Job Title *
              </label>
              <div className="relative">
                <Briefcase className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  id="title"
                  name="title"
                  type="text"
                  value={formData.title}
                  onChange={handleChange}
                  placeholder="e.g. Senior Machine Learning Engineer"
                  className={`w-full rounded-xl border pl-10 pr-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${
                    errors.title
                      ? 'border-rose-300 focus:ring-rose-100 bg-rose-50/20'
                      : 'border-slate-200 bg-white focus:border-brand-400 focus:ring-brand-100'
                  }`}
                />
              </div>
              {errors.title && <p className="mt-1 text-xs text-rose-600">{errors.title}</p>}
            </div>

            <div>
              <label htmlFor="company" className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                Hiring Organization / Company *
              </label>
              <div className="relative">
                <Building className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  id="company"
                  name="company"
                  type="text"
                  value={formData.company}
                  onChange={handleChange}
                  placeholder="e.g. NexusAI Technologies"
                  className={`w-full rounded-xl border pl-10 pr-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${
                    errors.company
                      ? 'border-rose-300 focus:ring-rose-100 bg-rose-50/20'
                      : 'border-slate-200 bg-white focus:border-brand-400 focus:ring-brand-100'
                  }`}
                />
              </div>
              {errors.company && <p className="mt-1 text-xs text-rose-600">{errors.company}</p>}
            </div>
          </div>

          {/* Row 2: Location & Employment Type */}
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label htmlFor="location" className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                Location *
              </label>
              <div className="relative">
                <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  id="location"
                  name="location"
                  type="text"
                  value={formData.location}
                  onChange={handleChange}
                  placeholder="e.g. Bengaluru / Remote"
                  className={`w-full rounded-xl border pl-10 pr-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${
                    errors.location
                      ? 'border-rose-300 focus:ring-rose-100 bg-rose-50/20'
                      : 'border-slate-200 bg-white focus:border-brand-400 focus:ring-brand-100'
                  }`}
                />
              </div>
              {errors.location && <p className="mt-1 text-xs text-rose-600">{errors.location}</p>}
            </div>

            <div>
              <label htmlFor="employmentType" className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                Employment Type
              </label>
              <select
                id="employmentType"
                name="employmentType"
                value={formData.employmentType}
                onChange={handleChange}
                className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
              >
                <option value="Full-time">Full-time</option>
                <option value="Part-time">Part-time</option>
                <option value="Contract">Contract</option>
                <option value="Internship">Internship</option>
              </select>
            </div>
          </div>

          {/* Row 3: Salary & Experience */}
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label htmlFor="salary" className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                Salary / Compensation Range *
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  id="salary"
                  name="salary"
                  type="text"
                  value={formData.salary}
                  onChange={handleChange}
                  placeholder="e.g. $120,000 - $150,000 / yr"
                  className={`w-full rounded-xl border pl-10 pr-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${
                    errors.salary
                      ? 'border-rose-300 focus:ring-rose-100 bg-rose-50/20'
                      : 'border-slate-200 bg-white focus:border-brand-400 focus:ring-brand-100'
                  }`}
                />
              </div>
              {errors.salary && <p className="mt-1 text-xs text-rose-600">{errors.salary}</p>}
            </div>

            <div>
              <label htmlFor="experience" className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                Required Experience *
              </label>
              <input
                id="experience"
                name="experience"
                type="text"
                value={formData.experience}
                onChange={handleChange}
                placeholder="e.g. 4+ years in Python & Deep Learning"
                className={`w-full rounded-xl border px-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${
                  errors.experience
                    ? 'border-rose-300 focus:ring-rose-100 bg-rose-50/20'
                    : 'border-slate-200 bg-white focus:border-brand-400 focus:ring-brand-100'
                }`}
              />
              {errors.experience && <p className="mt-1 text-xs text-rose-600">{errors.experience}</p>}
            </div>
          </div>

          {/* Row 4: Required Skills & Education */}
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label htmlFor="requiredSkills" className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                Required Skills (comma separated) *
              </label>
              <input
                id="requiredSkills"
                name="requiredSkills"
                type="text"
                value={formData.requiredSkills}
                onChange={handleChange}
                placeholder="e.g. PyTorch, Kubernetes, MLOps, Python"
                className={`w-full rounded-xl border px-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${
                  errors.requiredSkills
                    ? 'border-rose-300 focus:ring-rose-100 bg-rose-50/20'
                    : 'border-slate-200 bg-white focus:border-brand-400 focus:ring-brand-100'
                }`}
              />
              {errors.requiredSkills && <p className="mt-1 text-xs text-rose-600">{errors.requiredSkills}</p>}
            </div>

            <div>
              <label htmlFor="education" className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                Education Qualification
              </label>
              <div className="relative">
                <GraduationCap className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  id="education"
                  name="education"
                  type="text"
                  value={formData.education}
                  onChange={handleChange}
                  placeholder="e.g. B.Tech / M.S. in Computer Science"
                  className="w-full rounded-xl border border-slate-200 bg-white pl-10 pr-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
                />
              </div>
            </div>
          </div>

          {/* Job Description */}
          <div>
            <label htmlFor="jobDescription" className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
              Job Description & Core Responsibilities *
            </label>
            <textarea
              id="jobDescription"
              name="jobDescription"
              rows={5}
              value={formData.jobDescription}
              onChange={handleChange}
              placeholder="Outline the mission, primary duties, team structure, and impact of this role..."
              className={`w-full rounded-xl border p-3.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${
                errors.jobDescription
                  ? 'border-rose-300 focus:ring-rose-100 bg-rose-50/20'
                  : 'border-slate-200 bg-white focus:border-brand-400 focus:ring-brand-100'
              }`}
            />
            {errors.jobDescription && <p className="mt-1 text-xs text-rose-600">{errors.jobDescription}</p>}
          </div>

          {/* Submit Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => navigate('/hiring/dashboard')}
              className="rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 transition"
            >
              Cancel
            </button>

            <Button type="submit" disabled={loading} className="inline-flex items-center gap-2">
              {loading ? (
                <span>Publishing Job...</span>
              ) : (
                <>
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Publish Job Posting</span>
                </>
              )}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}

export default PostJobPage
