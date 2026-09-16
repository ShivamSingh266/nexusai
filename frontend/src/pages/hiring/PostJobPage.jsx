import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Briefcase,
  Building2,
  MapPin,
  DollarSign,
  GraduationCap,
  CheckCircle2,
  ArrowLeft,
  AlertCircle,
  Loader2,
  FileText,
  Clock,
} from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Toast } from '../../components/common/Toast'
import { hiringService } from '../../services/hiringService'

const initialForm = {
  title: '',
  location: '',
  employment_type: 'full_time',
  work_mode: 'hybrid',
  experience_min: '',
  experience_max: '',
  salary_min: '',
  salary_max: '',
  education_requirement: 'Bachelor’s Degree in Computer Science or related field',
  description: '',
  status: 'published',
}

export function PostJobPage() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState(initialForm)
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)
  const [companyMissingError, setCompanyMissingError] = useState(false)

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

    // Title validation (1 - 255 chars, required)
    const trimmedTitle = formData.title.trim()
    if (!trimmedTitle) {
      nextErrors.title = 'Job title is required.'
    } else if (trimmedTitle.length > 255) {
      nextErrors.title = 'Job title must not exceed 255 characters.'
    }

    // Location validation (max 255 chars)
    if (formData.location.trim().length > 255) {
      nextErrors.location = 'Location must not exceed 255 characters.'
    }

    // Education requirement validation (max 255 chars)
    if (formData.education_requirement.trim().length > 255) {
      nextErrors.education_requirement = 'Education requirement must not exceed 255 characters.'
    }

    // Experience validation
    const minExp = formData.experience_min !== '' ? Number.parseFloat(formData.experience_min) : null
    const maxExp = formData.experience_max !== '' ? Number.parseFloat(formData.experience_max) : null

    if (minExp !== null) {
      if (Number.isNaN(minExp) || minExp < 0) {
        nextErrors.experience_min = 'Minimum experience must be a non-negative number.'
      }
    }

    if (maxExp !== null) {
      if (Number.isNaN(maxExp) || maxExp < 0) {
        nextErrors.experience_max = 'Maximum experience must be a non-negative number.'
      }
    }

    if (minExp !== null && maxExp !== null && !nextErrors.experience_min && !nextErrors.experience_max) {
      if (minExp > maxExp) {
        nextErrors.experience_max = 'Maximum experience must be greater than or equal to minimum experience.'
      }
    }

    // Salary validation
    const minSal = formData.salary_min !== '' ? Number.parseFloat(formData.salary_min) : null
    const maxSal = formData.salary_max !== '' ? Number.parseFloat(formData.salary_max) : null

    if (minSal !== null) {
      if (Number.isNaN(minSal) || minSal < 0) {
        nextErrors.salary_min = 'Minimum salary must be a non-negative number.'
      }
    }

    if (maxSal !== null) {
      if (Number.isNaN(maxSal) || maxSal < 0) {
        nextErrors.salary_max = 'Maximum salary must be a non-negative number.'
      }
    }

    if (minSal !== null && maxSal !== null && !nextErrors.salary_min && !nextErrors.salary_max) {
      if (minSal > maxSal) {
        nextErrors.salary_max = 'Maximum salary must be greater than or equal to minimum salary.'
      }
    }

    return nextErrors
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (loading) return
    setCompanyMissingError(false)

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
      // Build backend-compatible JobCreate payload matching FastAPI schema
      const payload = {
        title: formData.title.trim(),
        description: formData.description.trim() || null,
        location: formData.location.trim() || null,
        employment_type: formData.employment_type || null,
        work_mode: formData.work_mode || null,
        experience_min:
          formData.experience_min !== '' && !Number.isNaN(Number(formData.experience_min))
            ? Number.parseFloat(formData.experience_min)
            : null,
        experience_max:
          formData.experience_max !== '' && !Number.isNaN(Number(formData.experience_max))
            ? Number.parseFloat(formData.experience_max)
            : null,
        salary_min:
          formData.salary_min !== '' && !Number.isNaN(Number(formData.salary_min))
            ? Number.parseFloat(formData.salary_min)
            : null,
        salary_max:
          formData.salary_max !== '' && !Number.isNaN(Number(formData.salary_max))
            ? Number.parseFloat(formData.salary_max)
            : null,
        education_requirement: formData.education_requirement.trim() || null,
        status: formData.status || 'published',
      }

      const res = await hiringService.createJob(payload)
      const jobData = res?.data || res

      let successMessage = `"${jobData?.title || formData.title}" is ${
        payload.status === 'published' ? 'published and ready for candidate matching' : 'saved as draft'
      }.`
      if (res?.warnings && Array.isArray(res.warnings) && res.warnings.length > 0) {
        successMessage += ` Note: ${res.warnings.join(', ')}`
      }

      setToast({
        variant: 'success',
        title: payload.status === 'published' ? 'Job Requisition Published' : 'Job Saved as Draft',
        message: successMessage,
      })

      // Reset form only on confirmed success
      setFormData(initialForm)

      // Navigate back to dashboard so recruiter can view the requisition
      setTimeout(() => {
        navigate('/hiring/dashboard')
      }, 1200)
    } catch (err) {
      const msg =
        typeof err?.message === 'string'
          ? err.message
          : Array.isArray(err?.detail)
            ? err.detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
            : 'Unable to post job.'

      if (msg.includes('company profile before managing job postings') || msg.includes('403')) {
        setCompanyMissingError(true)
        setToast({
          variant: 'warning',
          title: 'Company Profile Required',
          message: 'You must set up your company profile before managing job postings.',
        })
      } else {
        setToast({
          variant: 'error',
          title: 'Submission Failed',
          message: msg,
        })
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Toast Feedback Notification */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50">
          <Toast
            variant={toast.variant}
            title={toast.title}
            message={toast.message}
            duration={4500}
            onDismiss={() => setToast(null)}
          />
        </div>
      )}

      {/* Header */}
      <header className="flex flex-col gap-3 border-b border-slate-200 pb-6 dark:border-slate-800 md:flex-row md:items-center md:justify-between">
        <div>
          <button
            type="button"
            onClick={() => navigate('/hiring/dashboard')}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 transition mb-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Dashboard</span>
          </button>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Post a Job Opening
            </h1>
            <span className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-semibold text-brand-700 dark:bg-brand-950/50 dark:text-brand-300">
              Requisition
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Create an active job requisition with clear competency, qualification, and compensation benchmarks.
          </p>
        </div>
      </header>

      {/* Recruiter Company Profile Prerequisite Alert */}
      {companyMissingError && (
        <div
          role="alert"
          className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-200 flex items-start gap-3"
        >
          <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-sm font-bold text-amber-900 dark:text-amber-200">Company Profile Required</h4>
            <p className="text-xs text-amber-800 dark:text-amber-300 mt-1">
              Your recruiter account must have an active company profile before creating public job requisitions.
            </p>
            <button
              type="button"
              onClick={() => navigate('/hiring/company-profile')}
              className="mt-2.5 inline-flex items-center gap-1.5 rounded-lg bg-amber-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-amber-800 dark:bg-amber-600 dark:hover:bg-amber-700 transition"
            >
              <Building2 className="h-3.5 w-3.5" />
              <span>Create Company Profile Now</span>
            </button>
          </div>
        </div>
      )}

      {/* Job Creation Form Card */}
      <Card className="p-6 border border-slate-200 dark:border-slate-800 dark:bg-slate-900">
        <form onSubmit={handleSubmit} noValidate className="space-y-6">
          {/* Row 1: Title & Location */}
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label
                htmlFor="title"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5"
              >
                Job Title <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <Briefcase className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 dark:text-slate-500" />
                <input
                  id="title"
                  name="title"
                  type="text"
                  required
                  aria-invalid={Boolean(errors.title)}
                  aria-describedby={errors.title ? 'title-error' : undefined}
                  value={formData.title}
                  onChange={handleChange}
                  placeholder="e.g. Senior Machine Learning Engineer"
                  className={`w-full rounded-xl border pl-10 pr-3.5 py-2.5 text-sm text-slate-800 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 bg-white dark:bg-slate-800/80 transition focus:outline-none focus:ring-2 ${
                    errors.title
                      ? 'border-rose-300 dark:border-rose-500/60 bg-rose-50/20 dark:bg-rose-950/20 focus:ring-rose-500/20'
                      : 'border-slate-200 dark:border-slate-700 focus:border-brand-500 focus:ring-brand-500/20'
                  }`}
                />
              </div>
              {errors.title && (
                <p id="title-error" className="mt-1 text-xs font-medium text-rose-600 dark:text-rose-400">
                  {errors.title}
                </p>
              )}
            </div>

            <div>
              <label
                htmlFor="location"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5"
              >
                Location
              </label>
              <div className="relative">
                <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 dark:text-slate-500" />
                <input
                  id="location"
                  name="location"
                  type="text"
                  aria-invalid={Boolean(errors.location)}
                  aria-describedby={errors.location ? 'location-error' : undefined}
                  value={formData.location}
                  onChange={handleChange}
                  placeholder="e.g. Bengaluru, India / Remote"
                  className={`w-full rounded-xl border pl-10 pr-3.5 py-2.5 text-sm text-slate-800 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 bg-white dark:bg-slate-800/80 transition focus:outline-none focus:ring-2 ${
                    errors.location
                      ? 'border-rose-300 dark:border-rose-500/60 bg-rose-50/20 dark:bg-rose-950/20 focus:ring-rose-500/20'
                      : 'border-slate-200 dark:border-slate-700 focus:border-brand-500 focus:ring-brand-500/20'
                  }`}
                />
              </div>
              {errors.location && (
                <p id="location-error" className="mt-1 text-xs font-medium text-rose-600 dark:text-rose-400">
                  {errors.location}
                </p>
              )}
            </div>
          </div>

          {/* Row 2: Employment Type & Work Mode */}
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label
                htmlFor="employment_type"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5"
              >
                Employment Type
              </label>
              <select
                id="employment_type"
                name="employment_type"
                value={formData.employment_type}
                onChange={handleChange}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3.5 py-2.5 text-sm text-slate-800 dark:text-slate-100 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition"
              >
                <option value="full_time">Full-time</option>
                <option value="part_time">Part-time</option>
                <option value="contract">Contract</option>
                <option value="internship">Internship</option>
                <option value="freelance">Freelance</option>
              </select>
            </div>

            <div>
              <label
                htmlFor="work_mode"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5"
              >
                Work Mode
              </label>
              <select
                id="work_mode"
                name="work_mode"
                value={formData.work_mode}
                onChange={handleChange}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3.5 py-2.5 text-sm text-slate-800 dark:text-slate-100 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition"
              >
                <option value="hybrid">Hybrid</option>
                <option value="remote">Remote</option>
                <option value="onsite">On-site</option>
              </select>
            </div>
          </div>

          {/* Row 3: Experience Min & Max */}
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label
                htmlFor="experience_min"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5"
              >
                Minimum Experience (Years)
              </label>
              <div className="relative">
                <Clock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 dark:text-slate-500" />
                <input
                  id="experience_min"
                  name="experience_min"
                  type="number"
                  step="0.5"
                  min="0"
                  aria-invalid={Boolean(errors.experience_min)}
                  aria-describedby={errors.experience_min ? 'experience_min-error' : undefined}
                  value={formData.experience_min}
                  onChange={handleChange}
                  placeholder="e.g. 3"
                  className={`w-full rounded-xl border pl-10 pr-3.5 py-2.5 text-sm text-slate-800 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 bg-white dark:bg-slate-800/80 transition focus:outline-none focus:ring-2 ${
                    errors.experience_min
                      ? 'border-rose-300 dark:border-rose-500/60 bg-rose-50/20 dark:bg-rose-950/20 focus:ring-rose-500/20'
                      : 'border-slate-200 dark:border-slate-700 focus:border-brand-500 focus:ring-brand-500/20'
                  }`}
                />
              </div>
              {errors.experience_min && (
                <p id="experience_min-error" className="mt-1 text-xs font-medium text-rose-600 dark:text-rose-400">
                  {errors.experience_min}
                </p>
              )}
            </div>

            <div>
              <label
                htmlFor="experience_max"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5"
              >
                Maximum Experience (Years)
              </label>
              <div className="relative">
                <Clock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 dark:text-slate-500" />
                <input
                  id="experience_max"
                  name="experience_max"
                  type="number"
                  step="0.5"
                  min="0"
                  aria-invalid={Boolean(errors.experience_max)}
                  aria-describedby={errors.experience_max ? 'experience_max-error' : undefined}
                  value={formData.experience_max}
                  onChange={handleChange}
                  placeholder="e.g. 7"
                  className={`w-full rounded-xl border pl-10 pr-3.5 py-2.5 text-sm text-slate-800 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 bg-white dark:bg-slate-800/80 transition focus:outline-none focus:ring-2 ${
                    errors.experience_max
                      ? 'border-rose-300 dark:border-rose-500/60 bg-rose-50/20 dark:bg-rose-950/20 focus:ring-rose-500/20'
                      : 'border-slate-200 dark:border-slate-700 focus:border-brand-500 focus:ring-brand-500/20'
                  }`}
                />
              </div>
              {errors.experience_max && (
                <p id="experience_max-error" className="mt-1 text-xs font-medium text-rose-600 dark:text-rose-400">
                  {errors.experience_max}
                </p>
              )}
            </div>
          </div>

          {/* Row 4: Salary Min & Max */}
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label
                htmlFor="salary_min"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5"
              >
                Minimum Annual Compensation ($)
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 dark:text-slate-500" />
                <input
                  id="salary_min"
                  name="salary_min"
                  type="number"
                  min="0"
                  aria-invalid={Boolean(errors.salary_min)}
                  aria-describedby={errors.salary_min ? 'salary_min-error' : undefined}
                  value={formData.salary_min}
                  onChange={handleChange}
                  placeholder="e.g. 80000"
                  className={`w-full rounded-xl border pl-10 pr-3.5 py-2.5 text-sm text-slate-800 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 bg-white dark:bg-slate-800/80 transition focus:outline-none focus:ring-2 ${
                    errors.salary_min
                      ? 'border-rose-300 dark:border-rose-500/60 bg-rose-50/20 dark:bg-rose-950/20 focus:ring-rose-500/20'
                      : 'border-slate-200 dark:border-slate-700 focus:border-brand-500 focus:ring-brand-500/20'
                  }`}
                />
              </div>
              {errors.salary_min && (
                <p id="salary_min-error" className="mt-1 text-xs font-medium text-rose-600 dark:text-rose-400">
                  {errors.salary_min}
                </p>
              )}
            </div>

            <div>
              <label
                htmlFor="salary_max"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5"
              >
                Maximum Annual Compensation ($)
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 dark:text-slate-500" />
                <input
                  id="salary_max"
                  name="salary_max"
                  type="number"
                  min="0"
                  aria-invalid={Boolean(errors.salary_max)}
                  aria-describedby={errors.salary_max ? 'salary_max-error' : undefined}
                  value={formData.salary_max}
                  onChange={handleChange}
                  placeholder="e.g. 120000"
                  className={`w-full rounded-xl border pl-10 pr-3.5 py-2.5 text-sm text-slate-800 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 bg-white dark:bg-slate-800/80 transition focus:outline-none focus:ring-2 ${
                    errors.salary_max
                      ? 'border-rose-300 dark:border-rose-500/60 bg-rose-50/20 dark:bg-rose-950/20 focus:ring-rose-500/20'
                      : 'border-slate-200 dark:border-slate-700 focus:border-brand-500 focus:ring-brand-500/20'
                  }`}
                />
              </div>
              {errors.salary_max && (
                <p id="salary_max-error" className="mt-1 text-xs font-medium text-rose-600 dark:text-rose-400">
                  {errors.salary_max}
                </p>
              )}
            </div>
          </div>

          {/* Row 5: Education Requirement & Requisition Status */}
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label
                htmlFor="education_requirement"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5"
              >
                Education Requirement
              </label>
              <div className="relative">
                <GraduationCap className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 dark:text-slate-500" />
                <input
                  id="education_requirement"
                  name="education_requirement"
                  type="text"
                  aria-invalid={Boolean(errors.education_requirement)}
                  aria-describedby={errors.education_requirement ? 'education_requirement-error' : undefined}
                  value={formData.education_requirement}
                  onChange={handleChange}
                  placeholder="e.g. Bachelor's or Master's degree in Computer Science"
                  className={`w-full rounded-xl border pl-10 pr-3.5 py-2.5 text-sm text-slate-800 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 bg-white dark:bg-slate-800/80 transition focus:outline-none focus:ring-2 ${
                    errors.education_requirement
                      ? 'border-rose-300 dark:border-rose-500/60 bg-rose-50/20 dark:bg-rose-950/20 focus:ring-rose-500/20'
                      : 'border-slate-200 dark:border-slate-700 focus:border-brand-500 focus:ring-brand-500/20'
                  }`}
                />
              </div>
              {errors.education_requirement && (
                <p id="education_requirement-error" className="mt-1 text-xs font-medium text-rose-600 dark:text-rose-400">
                  {errors.education_requirement}
                </p>
              )}
            </div>

            <div>
              <label
                htmlFor="status"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5"
              >
                Publishing State
              </label>
              <select
                id="status"
                name="status"
                value={formData.status}
                onChange={handleChange}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3.5 py-2.5 text-sm text-slate-800 dark:text-slate-100 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition"
              >
                <option value="published">Published (Active on portal)</option>
                <option value="draft">Draft (Private recruiter view only)</option>
              </select>
            </div>
          </div>

          {/* Job Description */}
          <div>
            <label
              htmlFor="description"
              className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5"
            >
              Job Description & Responsibilities
            </label>
            <div className="relative">
              <textarea
                id="description"
                name="description"
                rows={5}
                value={formData.description}
                onChange={handleChange}
                placeholder="Detail the role objectives, expected competencies, day-to-day responsibilities, and team collaboration scope..."
                className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/80 p-3.5 text-sm text-slate-800 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition"
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col-reverse sm:flex-row items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <button
              type="button"
              disabled={loading}
              onClick={() => navigate('/hiring/dashboard')}
              className="w-full sm:w-auto rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-5 py-2.5 text-sm font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition disabled:opacity-50"
            >
              Cancel
            </button>

            <Button
              type="submit"
              disabled={loading}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 shadow-sm"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Publishing Requisition...</span>
                </>
              ) : (
                <>
                  {formData.status === 'published' ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : (
                    <FileText className="h-4 w-4" />
                  )}
                  <span>
                    {formData.status === 'published'
                      ? 'Publish Job Requisition'
                      : 'Save Job as Draft'}
                  </span>
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
