import { useEffect, useState } from 'react'
import { User, Mail, MapPin, Briefcase, GraduationCap, Phone, Calendar, Edit2 } from 'lucide-react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Toast } from '../../components/common/Toast'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { ProfileForm } from './ProfileForm'
import { applicantService } from '../../services/applicantService'
import { auth } from '../../services/auth'

export function ProfilePage() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [toast, setToast] = useState(null)
  const currentUser = auth.getUser()

  useEffect(() => {
    let ignore = false
    async function load() {
      try {
        const data = await applicantService.getProfile()
        if (!ignore) {
          setProfile(data)
        }
      } catch (err) {
        if (!ignore) {
          // If 404, user has not created a profile yet
          if (err?.message?.includes('404') || err?.message?.includes('not found')) {
            setProfile(null)
          } else {
            setToast({
              variant: 'error',
              title: 'Error loading profile',
              message: err?.message || 'Unable to connect to profile service.',
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
  }, [])

  const handleSaveProfile = async (formData) => {
    setSaving(true)
    try {
      if (profile?.id) {
        // Update existing profile (PUT)
        const updated = await applicantService.updateProfile(formData)
        setProfile(updated)
        setToast({
          variant: 'success',
          title: 'Profile Updated',
          message: 'Your profile changes have been saved.',
        })
      } else {
        // Create new profile (POST)
        const created = await applicantService.createProfile(formData)
        setProfile(created)
        setToast({
          variant: 'success',
          title: 'Profile Created',
          message: 'Your applicant profile has been initialized.',
        })
      }
      setIsEditing(false)
    } catch (err) {
      setToast({
        variant: 'error',
        title: 'Save Failed',
        message: err?.message || 'Unable to save profile.',
      })
    } finally {
      setSaving(false)
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
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Applicant</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Your Profile</h1>
          <p className="mt-1 text-sm text-slate-600">
            Keep your skills, verified background, and career aspirations current to maximize job match quality.
          </p>
        </div>

        {!loading && profile && !isEditing && (
          <Button onClick={() => setIsEditing(true)} className="inline-flex items-center gap-2">
            <Edit2 className="h-4 w-4" />
            <span>Edit Profile</span>
          </Button>
        )}
      </div>

      {loading ? (
        <div className="space-y-4">
          <LoadingSkeleton variant="card" />
          <LoadingSkeleton variant="card" />
        </div>
      ) : isEditing || !profile ? (
        <Card className="p-6">
          <div className="mb-6 pb-4 border-b border-slate-100">
            <h2 className="text-lg font-bold text-slate-900">
              {profile ? 'Edit Profile Details' : 'Complete Your Applicant Profile'}
            </h2>
            <p className="text-xs text-slate-500">
              {profile
                ? 'Update your bio, contact coordinates, and experience metrics.'
                : 'Initialize your talent profile to enable AI candidate matching.'}
            </p>
          </div>

          <ProfileForm
            initialData={profile || {}}
            onSubmit={handleSaveProfile}
            onCancel={profile ? () => setIsEditing(false) : undefined}
            loading={saving}
          />
        </Card>
      ) : (
        /* Profile View Mode */
        <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
          {/* Identity & Contact Card */}
          <Card className="p-6 space-y-6">
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 to-brand-800 text-xl font-bold text-white shadow-sm">
                {currentUser?.full_name
                  ? currentUser.full_name
                      .split(' ')
                      .map((n) => n[0])
                      .slice(0, 2)
                      .join('')
                  : 'A'}
              </div>

              <div>
                <h3 className="text-xl font-bold text-slate-900">
                  {currentUser?.full_name || 'Applicant'}
                </h3>
                <p className="text-xs font-semibold uppercase tracking-wider text-brand-700">
                  {currentUser?.role || 'Applicant'}
                </p>
              </div>
            </div>

            <div className="space-y-3 pt-4 border-t border-slate-100 text-xs text-slate-600">
              <div className="flex items-center gap-2.5">
                <Mail className="h-4 w-4 text-slate-400 shrink-0" />
                <span>{currentUser?.email}</span>
              </div>

              {profile.phone && (
                <div className="flex items-center gap-2.5">
                  <Phone className="h-4 w-4 text-slate-400 shrink-0" />
                  <span>{profile.phone}</span>
                </div>
              )}

              {profile.location && (
                <div className="flex items-center gap-2.5">
                  <MapPin className="h-4 w-4 text-slate-400 shrink-0" />
                  <span>{profile.location}</span>
                </div>
              )}

              {profile.experience_years !== null && profile.experience_years !== undefined && (
                <div className="flex items-center gap-2.5">
                  <Briefcase className="h-4 w-4 text-slate-400 shrink-0" />
                  <span>{profile.experience_years} years experience</span>
                </div>
              )}

              {profile.education && (
                <div className="flex items-center gap-2.5">
                  <GraduationCap className="h-4 w-4 text-slate-400 shrink-0" />
                  <span>{profile.education}</span>
                </div>
              )}

              {profile.gender && (
                <div className="flex items-center gap-2.5">
                  <User className="h-4 w-4 text-slate-400 shrink-0" />
                  <span>{profile.gender}</span>
                </div>
              )}

              {profile.date_of_birth && (
                <div className="flex items-center gap-2.5">
                  <Calendar className="h-4 w-4 text-slate-400 shrink-0" />
                  <span>Born: {profile.date_of_birth}</span>
                </div>
              )}
            </div>
          </Card>

          {/* Professional Bio / Summary Card */}
          <Card className="p-6 flex flex-col justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900 mb-3">Professional Bio</h3>
              <p className="text-sm leading-relaxed text-slate-700 whitespace-pre-line">
                {profile.bio || 'No bio provided yet. Click "Edit Profile" to add your summary.'}
              </p>
            </div>

            <div className="mt-8 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
              <span>Profile ID: #{profile.id}</span>
              <span>Account active</span>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}

export default ProfilePage
