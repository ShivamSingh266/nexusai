import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Building2,
  Globe,
  MapPin,
  Users,
  Edit2,
  Check,
  ArrowRight,
  Briefcase,
  AlertCircle,
  Loader2,
  LayoutDashboard,
  Calendar,
} from 'lucide-react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Toast } from '../../components/common/Toast'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { EmptyState } from '../../components/common/EmptyState'
import { hiringService } from '../../services/hiringService'
import { cn } from '../../lib/utils'

const initialCompanyForm = {
  company_name: '',
  industry: '',
  company_size: '51-200',
  location: '',
  website: '',
  description: '',
}

export function CompanyProfilePage() {
  const navigate = useNavigate()
  const [company, setCompany] = useState(null)
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState(initialCompanyForm)
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [apiError, setApiError] = useState(null)
  const [toast, setToast] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let ignore = false
    async function load() {
      setApiError(null)
      try {
        const res = await hiringService.getCompanyProfile()
        const data = res?.data || res
        if (data && (data.company_name || data.companyName)) {
          const normalized = {
            id: data.id,
            company_name: data.company_name || data.companyName || '',
            industry: data.industry || '',
            company_size: data.company_size || data.companySize || '51-200',
            location: data.location || '',
            website: data.website || '',
            description: data.description || '',
            created_at: data.created_at || data.createdAt,
            updated_at: data.updated_at || data.updatedAt,
          }
          if (!ignore) {
            setCompany(normalized)
            setFormData(normalized)
          }
        } else {
          if (!ignore) {
            setCompany(null)
          }
        }
      } catch (err) {
        if (!ignore) {
          // 404 indicates no company profile has been created yet (valid empty state)
          if (err?.message?.includes('404') || err?.message?.includes('No company profile found')) {
            setCompany(null)
          } else {
            setApiError(err?.message || 'Unable to connect to company profile service.')
            setToast({
              variant: 'error',
              title: 'Connection Error',
              message: err?.message || 'Unable to load company profile.',
            })
          }
        }
      } finally {
        if (!ignore) {
          setLoading(false)
        }
      }
    }

    load()
    return () => {
      ignore = true
    }
  }, [reloadKey])

  const handleRetry = () => {
    setLoading(true)
    setReloadKey((prev) => prev + 1)
  }

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
    const name = formData.company_name?.trim() || ''
    if (!name) {
      nextErrors.company_name = 'Company name is required.'
    } else if (name.length > 255) {
      nextErrors.company_name = 'Company name cannot exceed 255 characters.'
    }

    if (formData.industry && formData.industry.length > 150) {
      nextErrors.industry = 'Industry cannot exceed 150 characters.'
    }

    if (formData.location && formData.location.length > 255) {
      nextErrors.location = 'Location cannot exceed 255 characters.'
    }

    if (formData.company_size && formData.company_size.length > 50) {
      nextErrors.company_size = 'Company size cannot exceed 50 characters.'
    }

    if (formData.website?.trim()) {
      const site = formData.website.trim()
      if (site.length > 255) {
        nextErrors.website = 'Website URL cannot exceed 255 characters.'
      } else if (!/^https?:\/\//i.test(site) && !site.includes('.')) {
        nextErrors.website = 'Please enter a valid website URL (e.g. https://example.com).'
      }
    }

    return nextErrors
  }

  const handleSave = async (e) => {
    e.preventDefault()
    const validationErrors = validate()
    setErrors(validationErrors)

    if (Object.keys(validationErrors).length > 0) {
      setToast({
        variant: 'error',
        title: 'Validation Error',
        message: 'Please resolve the highlighted form errors before saving.',
      })
      return
    }

    setSaving(true)
    setApiError(null)
    try {
      let formattedWebsite = formData.website?.trim() || null
      if (formattedWebsite && !/^https?:\/\//i.test(formattedWebsite)) {
        formattedWebsite = `https://${formattedWebsite}`
      }

      const payload = {
        company_name: formData.company_name.trim(),
        description: formData.description?.trim() || null,
        industry: formData.industry?.trim() || null,
        website: formattedWebsite,
        location: formData.location?.trim() || null,
        company_size: formData.company_size?.trim() || null,
      }

      if (company?.id) {
        // Update existing company profile (PATCH /api/v1/recruiter/company)
        const updated = await hiringService.updateCompanyProfile(payload)
        const normalized = updated?.data || updated
        setCompany(normalized)
        setFormData({
          ...payload,
          id: normalized.id || company.id,
          created_at: normalized.created_at || company.created_at,
          updated_at: normalized.updated_at || new Date().toISOString(),
        })
        setToast({
          variant: 'success',
          title: 'Profile Updated',
          message: 'Company profile details have been saved successfully.',
        })
      } else {
        // Create new company profile (POST /api/v1/recruiter/company)
        const created = await hiringService.createCompanyProfile(payload)
        const normalized = created?.data || created
        setCompany(normalized)
        setFormData({
          ...payload,
          id: normalized.id || Date.now(),
          created_at: normalized.created_at || new Date().toISOString(),
          updated_at: normalized.updated_at || new Date().toISOString(),
        })
        setToast({
          variant: 'success',
          title: 'Company Profile Created',
          message: 'Your company profile has been created successfully.',
        })
      }
      setIsEditing(false)
    } catch (err) {
      const msg = err?.message || 'Unable to save company profile.'
      setApiError(msg)
      setToast({
        variant: 'error',
        title: 'Save Failed',
        message: msg,
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Toast Notification */}
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
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 dark:border-slate-800 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-600 dark:text-brand-400">
            Hiring
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Company Profile
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Manage your corporate identity, industry alignment, and organization settings.
          </p>
        </div>

        {/* Header Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          <Button
            variant="secondary"
            onClick={() => navigate('/hiring/dashboard')}
            className="inline-flex items-center gap-1.5 text-xs"
          >
            <LayoutDashboard className="h-3.5 w-3.5" />
            <span>Dashboard</span>
          </Button>

          {!loading && company && !isEditing && (
            <>
              <Button
                variant="secondary"
                onClick={() => navigate('/hiring/post-job')}
                className="inline-flex items-center gap-1.5 text-xs"
              >
                <Briefcase className="h-3.5 w-3.5" />
                <span>Post Job</span>
              </Button>

              <Button
                onClick={() => setIsEditing(true)}
                className="inline-flex items-center gap-1.5 text-xs"
              >
                <Edit2 className="h-3.5 w-3.5" />
                <span>Edit Profile</span>
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Error Alert Banner */}
      {apiError && (
        <div
          role="alert"
          className="flex items-center justify-between rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300"
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 flex-shrink-0 text-rose-600 dark:text-rose-400" />
            <span>{apiError}</span>
          </div>
          <Button
            variant="secondary"
            onClick={handleRetry}
            className="h-auto px-3 py-1.5 text-xs font-semibold"
          >
            Retry
          </Button>
        </div>
      )}

      {/* Main View Layout */}
      {loading ? (
        <div className="space-y-4">
          <LoadingSkeleton variant="card" className="h-44" />
          <LoadingSkeleton variant="card" className="h-64" />
        </div>
      ) : !company && !isEditing ? (
        /* Empty State: No Company Profile Set Up */
        <EmptyState
          title="No Company Profile Yet"
          description="You must create your recruiter company profile before you can publish job openings and review candidates."
          icon={<Building2 className="h-8 w-8 text-brand-600 dark:text-brand-400" />}
          actionLabel="Set Up Company Profile"
          onAction={() => {
            setFormData(initialCompanyForm)
            setIsEditing(true)
          }}
        />
      ) : isEditing || !company ? (
        /* Form: Create or Edit Profile */
        <Card className="border border-slate-200 bg-white/90 p-6 shadow-sm backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-8">
          <div className="mb-6 border-b border-slate-100 pb-4 dark:border-slate-800">
            <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
              {company ? 'Edit Company Information' : 'Set Up Company Profile'}
            </h2>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {company
                ? 'Update your organization particulars, website, and industry focus.'
                : 'Enter your organization details to establish your recruiter profile.'}
            </p>
          </div>

          <form onSubmit={handleSave} className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              {/* Company Name */}
              <div>
                <label
                  htmlFor="company_name"
                  className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300"
                >
                  Company Name <span className="text-rose-500">*</span>
                </label>
                <input
                  id="company_name"
                  name="company_name"
                  value={formData.company_name}
                  onChange={handleChange}
                  maxLength={255}
                  required
                  aria-required="true"
                  aria-invalid={Boolean(errors.company_name)}
                  aria-describedby={errors.company_name ? 'company_name-error' : undefined}
                  placeholder="e.g. NexusAI Technologies Inc."
                  className={cn(
                    'w-full rounded-xl border px-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 dark:text-slate-100 dark:placeholder:text-slate-500',
                    errors.company_name
                      ? 'border-rose-300 bg-rose-50/20 focus:ring-rose-500/20 dark:border-rose-700 dark:bg-rose-950/20'
                      : 'border-slate-200 bg-white focus:border-brand-500 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-800',
                  )}
                />
                {errors.company_name && (
                  <p
                    id="company_name-error"
                    role="alert"
                    className="mt-1 text-xs text-rose-600 dark:text-rose-400"
                  >
                    {errors.company_name}
                  </p>
                )}
              </div>

              {/* Industry */}
              <div>
                <label
                  htmlFor="industry"
                  className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300"
                >
                  Industry / Sector
                </label>
                <input
                  id="industry"
                  name="industry"
                  value={formData.industry}
                  onChange={handleChange}
                  maxLength={150}
                  aria-invalid={Boolean(errors.industry)}
                  aria-describedby={errors.industry ? 'industry-error' : undefined}
                  placeholder="e.g. Enterprise Software & AI"
                  className={cn(
                    'w-full rounded-xl border px-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 dark:text-slate-100 dark:placeholder:text-slate-500',
                    errors.industry
                      ? 'border-rose-300 bg-rose-50/20 focus:ring-rose-500/20 dark:border-rose-700 dark:bg-rose-950/20'
                      : 'border-slate-200 bg-white focus:border-brand-500 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-800',
                  )}
                />
                {errors.industry && (
                  <p
                    id="industry-error"
                    role="alert"
                    className="mt-1 text-xs text-rose-600 dark:text-rose-400"
                  >
                    {errors.industry}
                  </p>
                )}
              </div>

              {/* Location */}
              <div>
                <label
                  htmlFor="location"
                  className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300"
                >
                  Headquarters Location
                </label>
                <input
                  id="location"
                  name="location"
                  value={formData.location}
                  onChange={handleChange}
                  maxLength={255}
                  aria-invalid={Boolean(errors.location)}
                  aria-describedby={errors.location ? 'location-error' : undefined}
                  placeholder="e.g. Bengaluru, India"
                  className={cn(
                    'w-full rounded-xl border px-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 dark:text-slate-100 dark:placeholder:text-slate-500',
                    errors.location
                      ? 'border-rose-300 bg-rose-50/20 focus:ring-rose-500/20 dark:border-rose-700 dark:bg-rose-950/20'
                      : 'border-slate-200 bg-white focus:border-brand-500 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-800',
                  )}
                />
                {errors.location && (
                  <p
                    id="location-error"
                    role="alert"
                    className="mt-1 text-xs text-rose-600 dark:text-rose-400"
                  >
                    {errors.location}
                  </p>
                )}
              </div>

              {/* Company Size */}
              <div>
                <label
                  htmlFor="company_size"
                  className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300"
                >
                  Company Size
                </label>
                <select
                  id="company_size"
                  name="company_size"
                  value={formData.company_size}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
                >
                  <option value="1-10">1-10 Employees</option>
                  <option value="11-50">11-50 Employees</option>
                  <option value="51-200">51-200 Employees</option>
                  <option value="201-500">201-500 Employees</option>
                  <option value="500+">500+ Employees</option>
                </select>
              </div>

              {/* Website URL */}
              <div className="md:col-span-2">
                <label
                  htmlFor="website"
                  className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300"
                >
                  Official Website URL
                </label>
                <input
                  id="website"
                  name="website"
                  type="text"
                  value={formData.website}
                  onChange={handleChange}
                  maxLength={255}
                  aria-invalid={Boolean(errors.website)}
                  aria-describedby={errors.website ? 'website-error' : undefined}
                  placeholder="https://nexusai.example"
                  className={cn(
                    'w-full rounded-xl border px-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 dark:text-slate-100 dark:placeholder:text-slate-500',
                    errors.website
                      ? 'border-rose-300 bg-rose-50/20 focus:ring-rose-500/20 dark:border-rose-700 dark:bg-rose-950/20'
                      : 'border-slate-200 bg-white focus:border-brand-500 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-800',
                  )}
                />
                {errors.website && (
                  <p
                    id="website-error"
                    role="alert"
                    className="mt-1 text-xs text-rose-600 dark:text-rose-400"
                  >
                    {errors.website}
                  </p>
                )}
              </div>
            </div>

            {/* Overview / Description */}
            <div>
              <label
                htmlFor="description"
                className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300"
              >
                Company Overview & Mission
              </label>
              <textarea
                id="description"
                name="description"
                rows={4}
                value={formData.description}
                onChange={handleChange}
                placeholder="Describe your organizational mission, core technological focus, and workplace culture..."
                className="w-full rounded-xl border border-slate-200 bg-white p-3.5 text-sm text-slate-800 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-500"
              />
            </div>

            {/* Form Buttons */}
            <div className="flex items-center justify-end gap-3 border-t border-slate-100 pt-4 dark:border-slate-800">
              {company && (
                <button
                  type="button"
                  onClick={() => {
                    setFormData(company)
                    setErrors({})
                    setIsEditing(false)
                  }}
                  className="rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-600 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-750"
                >
                  Cancel
                </button>
              )}

              <Button
                type="submit"
                disabled={saving}
                className="inline-flex items-center gap-2"
              >
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Saving Profile...</span>
                  </>
                ) : (
                  <>
                    <Check className="h-4 w-4" />
                    <span>{company ? 'Save Changes' : 'Create Company Profile'}</span>
                  </>
                )}
              </Button>
            </div>
          </form>
        </Card>
      ) : (
        /* Read-Only Profile View */
        <Card className="space-y-6 border border-slate-200 bg-white/90 p-6 shadow-sm backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/90 sm:p-8">
          {/* Identity Header */}
          <div className="flex flex-col items-start gap-5 border-b border-slate-100 pb-6 dark:border-slate-800 sm:flex-row">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 to-brand-800 text-2xl font-bold text-white shadow-md">
              {company?.company_name?.charAt(0) || 'C'}
            </div>

            <div className="flex-1">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  {company?.company_name}
                </h2>
                <span className="inline-flex items-center rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                  Active Recruiter Account
                </span>
              </div>

              <div className="mt-2.5 flex flex-wrap items-center gap-4 text-xs text-slate-600 dark:text-slate-400">
                {company?.industry && (
                  <span className="flex items-center gap-1.5 font-medium">
                    <Building2 className="h-3.5 w-3.5 text-slate-400 dark:text-slate-500" />
                    <span>{company.industry}</span>
                  </span>
                )}
                {company?.location && (
                  <span className="flex items-center gap-1.5 font-medium">
                    <MapPin className="h-3.5 w-3.5 text-slate-400 dark:text-slate-500" />
                    <span>{company.location}</span>
                  </span>
                )}
                {company?.company_size && (
                  <span className="flex items-center gap-1.5 font-medium">
                    <Users className="h-3.5 w-3.5 text-slate-400 dark:text-slate-500" />
                    <span>{company.company_size} Employees</span>
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Description / Overview */}
          <div className="space-y-4">
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                About the Organization
              </h3>
              <p className="text-sm leading-relaxed text-slate-700 whitespace-pre-line dark:text-slate-300">
                {company?.description || 'No organizational description provided yet.'}
              </p>
            </div>

            {/* Online Presence & Timestamps */}
            <div className="grid gap-4 border-t border-slate-100 pt-4 text-xs dark:border-slate-800 sm:grid-cols-2">
              {company?.website ? (
                <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                  <Globe className="h-4 w-4 text-slate-400 dark:text-slate-500" />
                  <a
                    href={company.website}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium text-brand-600 transition hover:underline dark:text-brand-400"
                  >
                    {company.website}
                  </a>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-slate-400 dark:text-slate-500">
                  <Globe className="h-4 w-4" />
                  <span>No website URL provided</span>
                </div>
              )}

              {company?.created_at && (
                <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 sm:justify-end">
                  <Calendar className="h-4 w-4 text-slate-400 dark:text-slate-500" />
                  <span>Profile established {new Date(company.created_at).toLocaleDateString()}</span>
                </div>
              )}
            </div>
          </div>

          {/* Connected Hiring Workflow Callout */}
          <div className="flex flex-col gap-3 rounded-2xl border border-brand-200/70 bg-brand-50/50 p-4.5 dark:border-brand-900/40 dark:bg-brand-950/30 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-brand-700 dark:text-brand-300">
                Job Requisitions & Hiring
              </p>
              <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-400">
                Your company profile is active. Ready to create a new job opening or review applications?
              </p>
            </div>

            <Button
              onClick={() => navigate('/hiring/post-job')}
              className="inline-flex items-center gap-1.5 self-start text-xs font-semibold sm:self-auto"
            >
              <span>Post a Job</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </div>
        </Card>
      )}
    </div>
  )
}

export default CompanyProfilePage
