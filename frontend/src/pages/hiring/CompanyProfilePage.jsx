import { useEffect, useMemo, useState } from 'react'
import { AppShell } from '../../components/layout/AppShell'
import { PageContainer } from '../../components/layout/PageContainer'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { useAuth } from '../../auth/AuthContext'
import { ApiError } from '../../services/api'
import { createCompany, getCompany, updateCompany } from '../../services/recruiter'

const emptyProfile = {
  company_name: '',
  industry: '',
  company_size: '',
  location: '',
  website: '',
  description: '',
}

const toProfile = (company) => ({
  company_name: company.company_name || '',
  industry: company.industry || '',
  company_size: company.company_size || '',
  location: company.location || '',
  website: company.website || '',
  description: company.description || '',
})

export function CompanyProfilePage() {
  const { accessToken } = useAuth()
  const [profile, setProfile] = useState(emptyProfile)
  const [isEditing, setIsEditing] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [notFound, setNotFound] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [loadAttempt, setLoadAttempt] = useState(0)

  useEffect(() => {
    let active = true
    getCompany(accessToken)
      .then((company) => {
        if (active) {
          setProfile(toProfile(company))
          setIsEditing(false)
        }
      })
      .catch((requestError) => {
        if (!active) return
        if (requestError instanceof ApiError && requestError.status === 404) {
          setNotFound(true)
          setIsEditing(true)
        } else {
          setLoadError(requestError.message)
          setIsEditing(false)
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [accessToken, loadAttempt])

  const completion = useMemo(() => {
    const fields = Object.values(profile)
    return Math.round((fields.filter(Boolean).length / fields.length) * 100)
  }, [profile])

  const handleChange = (event) => {
    const { name, value } = event.target
    setProfile((current) => ({ ...current, [name]: value }))
    setError('')
  }

  const retryLoad = () => {
    setLoading(true)
    setLoadError('')
    setError('')
    setNotFound(false)
    setLoadAttempt((current) => current + 1)
  }

  const handleSave = async () => {
    if (!profile.company_name.trim()) {
      setError('Company name is required.')
      return
    }

    setSaving(true)
    setError('')
    setNotice('')
    try {
      const payload = {
        ...profile,
        company_name: profile.company_name.trim(),
      }
      const company = notFound
        ? await createCompany(payload, accessToken)
        : await updateCompany(payload, accessToken)
      setProfile(toProfile(company))
      setNotFound(false)
      setIsEditing(false)
      setNotice('Company profile saved.')
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <AppShell title="Hiring Dashboard"><PageContainer><p className="text-sm text-slate-600">Loading company profile...</p></PageContainer></AppShell>
  }

  if (loadError) {
    return (
      <AppShell title="Hiring Dashboard">
        <PageContainer>
          <Card className="p-6">
            <h1 className="text-xl font-semibold text-slate-900">Unable to load company profile</h1>
            <p className="mt-2 text-sm text-red-700">{loadError}</p>
            <Button type="button" className="mt-5" onClick={retryLoad}>Retry</Button>
          </Card>
        </PageContainer>
      </AppShell>
    )
  }

  return (
    <AppShell title="Hiring Dashboard">
      <PageContainer>
        <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Hiring</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Company Profile</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">Keep your company details current for your hiring workspace.</p>
          </div>
          {!notFound ? <Button type="button" onClick={() => setIsEditing((current) => !current)}>{isEditing ? 'Close Edit' : 'Edit Profile'}</Button> : null}
        </div>

        {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {notice ? <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{notice}</p> : null}

        <Card className="overflow-hidden">
          <div className="bg-gradient-to-r from-brand-50 via-white to-slate-50 p-5 sm:p-6">
            <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
              <div className="flex items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 to-brand-800 text-xl font-bold text-white shadow-soft">
                  {profile.company_name.slice(0, 1).toUpperCase() || 'C'}
                </div>
                <div>
                  <div className="text-xl font-bold text-slate-900">{profile.company_name || 'Create your company profile'}</div>
                  <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-slate-600">
                    <span>{profile.industry || 'Industry not set'}</span>
                    <span>•</span>
                    <span>{profile.location || 'Location not set'}</span>
                  </div>
                </div>
              </div>
              <div className="rounded-full border border-brand-100 bg-white px-3 py-1.5 text-xs font-medium text-brand-700">{completion}% complete</div>
            </div>
            <p className="mt-5 max-w-3xl text-sm leading-6 text-slate-600">{profile.description || 'Add a description for your company.'}</p>
          </div>
        </Card>

        <Card className="p-5 sm:p-6">
          <h2 className="mb-5 text-xl font-semibold text-slate-900">Company Information</h2>
          <div className="grid gap-5 md:grid-cols-2">
            {[
              ['company_name', 'Company Name'],
              ['industry', 'Industry'],
              ['company_size', 'Company Size'],
              ['location', 'Location'],
              ['website', 'Website'],
            ].map(([name, label]) => (
              <label key={name} className="block text-sm font-medium text-slate-700">
                {label}
                <input name={name} value={profile[name]} onChange={handleChange} disabled={!isEditing} className={`mt-2 w-full rounded-xl border px-3.5 py-2.5 text-sm ${!isEditing ? 'cursor-not-allowed bg-slate-50 text-slate-500' : 'bg-white'}`} />
              </label>
            ))}
          </div>
          <label className="mt-5 block text-sm font-medium text-slate-700">
            Company Description
            <textarea name="description" value={profile.description} onChange={handleChange} disabled={!isEditing} rows={6} className={`mt-2 w-full rounded-xl border px-3.5 py-2.5 text-sm ${!isEditing ? 'cursor-not-allowed bg-slate-50 text-slate-500' : 'bg-white'}`} />
          </label>
        </Card>

        {isEditing ? (
          <div className="flex justify-end gap-3 pt-6">
            {!notFound ? <Button type="button" variant="secondary" onClick={() => setIsEditing(false)}>Cancel</Button> : null}
            <Button type="button" onClick={handleSave} disabled={saving}>{saving ? 'Saving...' : notFound ? 'Create Company' : 'Save Changes'}</Button>
          </div>
        ) : null}
      </PageContainer>
    </AppShell>
  )
}
