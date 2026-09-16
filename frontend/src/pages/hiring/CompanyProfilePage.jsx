import { useEffect, useState } from 'react'
import { Building2, Globe, MapPin, Users, Mail, Phone, Edit2, Check, ArrowLeft } from 'lucide-react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Toast } from '../../components/common/Toast'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { hiringService } from '../../services/hiringService'

export function CompanyProfilePage() {
  const [profile, setProfile] = useState(null)
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState({})
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    async function loadCompany() {
      try {
        const res = await hiringService.getCompanyProfile()
        const data = res?.data || res
        setProfile(data)
        setFormData(data)
      } finally {
        setLoading(false)
      }
    }
    loadCompany()
  }, [])

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
    if (!formData.companyName?.trim()) nextErrors.companyName = 'Company name is required.'
    if (!formData.industry?.trim()) nextErrors.industry = 'Industry is required.'
    if (!formData.location?.trim()) nextErrors.location = 'Location is required.'
    if (!formData.description?.trim()) nextErrors.description = 'Description is required.'
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
        message: 'Please fill in all mandatory fields.',
      })
      return
    }

    setSaving(true)
    try {
      await hiringService.updateCompanyProfile(formData)
      setProfile(formData)
      setIsEditing(false)
      setToast({
        variant: 'success',
        title: 'Profile Updated',
        message: 'Company profile details have been saved successfully.',
      })
    } catch {
      // Offline fallback: save locally
      setProfile(formData)
      setIsEditing(false)
      setToast({
        variant: 'success',
        title: 'Profile Updated Locally',
        message: 'Changes saved in active session.',
      })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 max-w-4xl mx-auto">
        <LoadingSkeleton variant="card" />
        <LoadingSkeleton variant="card" />
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
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
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Hiring</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Company Profile</h1>
          <p className="mt-2 text-sm text-slate-600">
            Maintain organizational credentials, industry taxonomy, and recruitment brand presence.
          </p>
        </div>

        {!isEditing ? (
          <Button onClick={() => setIsEditing(true)} className="inline-flex items-center gap-2">
            <Edit2 className="h-4 w-4" />
            <span>Edit Profile</span>
          </Button>
        ) : (
          <button
            type="button"
            onClick={() => {
              setFormData(profile)
              setIsEditing(false)
            }}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition"
          >
            Cancel
          </button>
        )}
      </div>

      {!isEditing ? (
        /* Read-only view */
        <div className="space-y-6">
          <Card className="p-6">
            <div className="flex flex-col sm:flex-row items-start gap-4 pb-6 border-b border-slate-100">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 to-brand-800 text-2xl font-bold text-white shadow-md">
                {profile?.companyName?.charAt(0) || 'C'}
              </div>

              <div className="flex-1">
                <h2 className="text-2xl font-bold text-slate-900">{profile?.companyName}</h2>
                <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-600">
                  <span className="flex items-center gap-1 font-medium">
                    <Building2 className="h-3.5 w-3.5 text-slate-400" />
                    {profile?.industry}
                  </span>
                  <span className="flex items-center gap-1 font-medium">
                    <MapPin className="h-3.5 w-3.5 text-slate-400" />
                    {profile?.location}
                  </span>
                  <span className="flex items-center gap-1 font-medium">
                    <Users className="h-3.5 w-3.5 text-slate-400" />
                    {profile?.companySize} Employees
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-6 space-y-4">
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                  About the Company
                </h3>
                <p className="text-sm leading-relaxed text-slate-700">{profile?.description}</p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 pt-4 border-t border-slate-100 text-xs">
                <div className="flex items-center gap-2 text-slate-600">
                  <Globe className="h-4 w-4 text-slate-400" />
                  <a
                    href={profile?.website}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium text-brand-700 hover:underline"
                  >
                    {profile?.website}
                  </a>
                </div>

                <div className="flex items-center gap-2 text-slate-600">
                  <Mail className="h-4 w-4 text-slate-400" />
                  <span>{profile?.contactEmail}</span>
                </div>

                {profile?.phone && (
                  <div className="flex items-center gap-2 text-slate-600">
                    <Phone className="h-4 w-4 text-slate-400" />
                    <span>{profile.phone}</span>
                  </div>
                )}

                {profile?.foundedYear && (
                  <div className="text-slate-600">
                    <span className="font-semibold text-slate-700">Founded:</span> {profile.foundedYear}
                  </div>
                )}
              </div>
            </div>
          </Card>
        </div>
      ) : (
        /* Edit mode */
        <Card className="p-6">
          <form onSubmit={handleSave} className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                  Company Name *
                </label>
                <input
                  name="companyName"
                  value={formData.companyName || ''}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
                />
                {errors.companyName && <p className="mt-1 text-xs text-rose-600">{errors.companyName}</p>}
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                  Industry / Domain *
                </label>
                <input
                  name="industry"
                  value={formData.industry || ''}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
                />
                {errors.industry && <p className="mt-1 text-xs text-rose-600">{errors.industry}</p>}
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                  Headquarters Location *
                </label>
                <input
                  name="location"
                  value={formData.location || ''}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
                />
                {errors.location && <p className="mt-1 text-xs text-rose-600">{errors.location}</p>}
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                  Company Size
                </label>
                <select
                  name="companySize"
                  value={formData.companySize || '50-200'}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
                >
                  <option value="1-10">1-10 Employees</option>
                  <option value="11-50">11-50 Employees</option>
                  <option value="51-200">51-200 Employees</option>
                  <option value="201-500">201-500 Employees</option>
                  <option value="500+">500+ Employees</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                  Website URL
                </label>
                <input
                  name="website"
                  value={formData.website || ''}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                  Contact Email
                </label>
                <input
                  name="contactEmail"
                  type="email"
                  value={formData.contactEmail || ''}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                Company Description *
              </label>
              <textarea
                name="description"
                rows={4}
                value={formData.description || ''}
                onChange={handleChange}
                className="w-full rounded-xl border border-slate-200 bg-white p-3.5 text-sm text-slate-800 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
              />
              {errors.description && <p className="mt-1 text-xs text-rose-600">{errors.description}</p>}
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition"
              >
                Cancel
              </button>

              <Button type="submit" disabled={saving} className="inline-flex items-center gap-2">
                <Check className="h-4 w-4" />
                <span>{saving ? 'Saving...' : 'Save Changes'}</span>
              </Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  )
}

export default CompanyProfilePage
