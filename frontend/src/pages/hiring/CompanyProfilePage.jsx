import { useMemo, useState } from 'react'
import { AppShell } from '../../components/layout/AppShell'
import { PageContainer } from '../../components/layout/PageContainer'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { companyProfile } from '../../mocks/companyProfileMockData'

const initialProfile = {
  companyName: companyProfile.companyName,
  industry: companyProfile.industry,
  companySize: companyProfile.companySize,
  location: companyProfile.location,
  website: companyProfile.website,
  contactEmail: companyProfile.contactEmail,
  phone: companyProfile.phone,
  foundedYear: companyProfile.foundedYear,
  description: companyProfile.description,
}

export function CompanyProfilePage() {
  const [profile, setProfile] = useState(initialProfile)
  const [isEditing, setIsEditing] = useState(false)
  const [errors, setErrors] = useState({})

  const completion = useMemo(() => {
    const fields = Object.values(profile)
    const filled = fields.filter((value) => String(value).trim()).length
    return Math.round((filled / fields.length) * 100)
  }, [profile])

  const handleChange = (event) => {
    const { name, value } = event.target
    setProfile((current) => ({ ...current, [name]: value }))
    setErrors((current) => ({ ...current, [name]: '' }))
  }

  const validateProfile = () => {
    const nextErrors = {}

    if (!profile.companyName.trim()) nextErrors.companyName = 'Company name is required.'
    if (!profile.industry.trim()) nextErrors.industry = 'Industry is required.'
    if (!profile.location.trim()) nextErrors.location = 'Location is required.'
    if (!profile.contactEmail.trim()) nextErrors.contactEmail = 'Contact email is required.'
    if (!profile.description.trim()) nextErrors.description = 'Company description is required.'

    if (profile.contactEmail && !/\S+@\S+\.\S+/.test(profile.contactEmail)) {
      nextErrors.contactEmail = 'Enter a valid email address.'
    }

    return nextErrors
  }

  const handleSave = () => {
    const nextErrors = validateProfile()
    setErrors(nextErrors)

    if (Object.keys(nextErrors).length > 0) {
      return
    }

    setIsEditing(false)
    window.alert('Frontend-only company profile saved. No backend call was made.')
  }

  const handleCancel = () => {
    setProfile(initialProfile)
    setErrors({})
    setIsEditing(false)
  }

  return (
    <AppShell title="Hiring Dashboard">
      <PageContainer>
        <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Hiring</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Company Profile</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              Keep your company details current and help recruiters and hiring teams review your profile quickly.
            </p>
          </div>

          <Button type="button" onClick={() => setIsEditing((current) => !current)}>
            {isEditing ? 'Close Edit' : 'Edit Profile'}
          </Button>
        </div>

        <Card className="overflow-hidden">
          <div className="bg-gradient-to-r from-brand-50 via-white to-slate-50 p-5 sm:p-6">
            <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
              <div className="flex items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 to-brand-800 text-xl font-bold text-white shadow-soft">
                  {profile.companyName.slice(0, 1)}
                </div>

                <div>
                  <div className="text-xl font-bold text-slate-900">{profile.companyName}</div>
                  <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-slate-600">
                    <span>{profile.industry}</span>
                    <span>•</span>
                    <span>{profile.location}</span>
                  </div>
                </div>
              </div>

              <div className="rounded-full border border-brand-100 bg-white px-3 py-1.5 text-xs font-medium text-brand-700">
                {completion}% complete
              </div>
            </div>

            <p className="mt-5 max-w-3xl text-sm leading-6 text-slate-600">{profile.description}</p>
          </div>
        </Card>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Card className="p-5">
            <p className="text-sm text-slate-500">Active Jobs</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">{companyProfile.hiringStats.activeJobs}</p>
          </Card>
          <Card className="p-5">
            <p className="text-sm text-slate-500">Total Applications</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">{companyProfile.hiringStats.totalApplications}</p>
          </Card>
          <Card className="p-5">
            <p className="text-sm text-slate-500">Shortlisted</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">{companyProfile.hiringStats.shortlistedCandidates}</p>
          </Card>
          <Card className="p-5">
            <p className="text-sm text-slate-500">Hiring Status</p>
            <p className="mt-3 text-xl font-bold text-slate-900">{companyProfile.hiringStats.hiringStatus}</p>
          </Card>
        </section>

        <Card className="p-5 sm:p-6">
          <div className="mb-5 flex items-center justify-between gap-3">
            <h2 className="text-xl font-semibold text-slate-900">Company Information</h2>
          </div>

          <div className="grid gap-5 md:grid-cols-2">
            <label className="block text-sm font-medium text-slate-700">
              Company Name
              <input
                name="companyName"
                value={profile.companyName}
                onChange={handleChange}
                disabled={!isEditing}
                className={`mt-2 w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100 ${
                  errors.companyName ? 'border-red-300 bg-red-50' : 'border-slate-200'
                } ${!isEditing ? 'cursor-not-allowed bg-slate-50 text-slate-500' : ''}`}
              />
              {errors.companyName ? <span className="mt-1 inline-block text-xs text-red-600">{errors.companyName}</span> : null}
            </label>

            <label className="block text-sm font-medium text-slate-700">
              Industry
              <input
                name="industry"
                value={profile.industry}
                onChange={handleChange}
                disabled={!isEditing}
                className={`mt-2 w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100 ${
                  errors.industry ? 'border-red-300 bg-red-50' : 'border-slate-200'
                } ${!isEditing ? 'cursor-not-allowed bg-slate-50 text-slate-500' : ''}`}
              />
              {errors.industry ? <span className="mt-1 inline-block text-xs text-red-600">{errors.industry}</span> : null}
            </label>

            <label className="block text-sm font-medium text-slate-700">
              Company Size
              <input
                name="companySize"
                value={profile.companySize}
                onChange={handleChange}
                disabled={!isEditing}
                className={`mt-2 w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100 ${
                  errors.companySize ? 'border-red-300 bg-red-50' : 'border-slate-200'
                } ${!isEditing ? 'cursor-not-allowed bg-slate-50 text-slate-500' : ''}`}
              />
            </label>

            <label className="block text-sm font-medium text-slate-700">
              Location
              <input
                name="location"
                value={profile.location}
                onChange={handleChange}
                disabled={!isEditing}
                className={`mt-2 w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100 ${
                  errors.location ? 'border-red-300 bg-red-50' : 'border-slate-200'
                } ${!isEditing ? 'cursor-not-allowed bg-slate-50 text-slate-500' : ''}`}
              />
              {errors.location ? <span className="mt-1 inline-block text-xs text-red-600">{errors.location}</span> : null}
            </label>

            <label className="block text-sm font-medium text-slate-700">
              Website
              <input
                name="website"
                value={profile.website}
                onChange={handleChange}
                disabled={!isEditing}
                className={`mt-2 w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100 ${
                  errors.website ? 'border-red-300 bg-red-50' : 'border-slate-200'
                } ${!isEditing ? 'cursor-not-allowed bg-slate-50 text-slate-500' : ''}`}
              />
            </label>

            <label className="block text-sm font-medium text-slate-700">
              Contact Email
              <input
                name="contactEmail"
                value={profile.contactEmail}
                onChange={handleChange}
                disabled={!isEditing}
                className={`mt-2 w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100 ${
                  errors.contactEmail ? 'border-red-300 bg-red-50' : 'border-slate-200'
                } ${!isEditing ? 'cursor-not-allowed bg-slate-50 text-slate-500' : ''}`}
              />
              {errors.contactEmail ? <span className="mt-1 inline-block text-xs text-red-600">{errors.contactEmail}</span> : null}
            </label>

            <label className="block text-sm font-medium text-slate-700">
              Phone
              <input
                name="phone"
                value={profile.phone}
                onChange={handleChange}
                disabled={!isEditing}
                className={`mt-2 w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100 ${
                  errors.phone ? 'border-red-300 bg-red-50' : 'border-slate-200'
                } ${!isEditing ? 'cursor-not-allowed bg-slate-50 text-slate-500' : ''}`}
              />
            </label>

            <label className="block text-sm font-medium text-slate-700">
              Founded Year
              <input
                name="foundedYear"
                value={profile.foundedYear}
                onChange={handleChange}
                disabled={!isEditing}
                className={`mt-2 w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100 ${
                  errors.foundedYear ? 'border-red-300 bg-red-50' : 'border-slate-200'
                } ${!isEditing ? 'cursor-not-allowed bg-slate-50 text-slate-500' : ''}`}
              />
            </label>
          </div>
        </Card>

        <Card className="p-5 sm:p-6">
          <h2 className="text-xl font-semibold text-slate-900">About Company</h2>
          <label className="mt-4 block text-sm font-medium text-slate-700">
            Company Description
            <textarea
              name="description"
              value={profile.description}
              onChange={handleChange}
              disabled={!isEditing}
              rows={6}
              className={`mt-2 w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100 ${
                errors.description ? 'border-red-300 bg-red-50' : 'border-slate-200'
              } ${!isEditing ? 'cursor-not-allowed bg-slate-50 text-slate-500' : ''}`}
            />
            {errors.description ? <span className="mt-1 inline-block text-xs text-red-600">{errors.description}</span> : null}
          </label>
        </Card>

        <Card className="p-5 sm:p-6">
          <div className="mb-5">
            <h2 className="text-xl font-semibold text-slate-900">Company Skills / Hiring Areas</h2>
          </div>

          <div className="flex flex-wrap gap-2">
            {companyProfile.focusAreas.map((area) => (
              <span
                key={area}
                className="rounded-full bg-brand-50 px-3 py-1.5 text-xs font-medium text-brand-700 ring-1 ring-brand-100"
              >
                {area}
              </span>
            ))}
          </div>
        </Card>

        {isEditing ? (
          <div className="flex flex-col justify-end gap-3 pt-6 sm:flex-row">
            <Button type="button" variant="secondary" onClick={handleCancel}>
              Cancel
            </Button>
            <Button type="button" onClick={handleSave}>
              Save Changes
            </Button>
          </div>
        ) : null}
      </PageContainer>
    </AppShell>
  )
}
