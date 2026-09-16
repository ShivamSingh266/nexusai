import { useState } from 'react'
import { Button } from '../../components/ui/Button'

export function ProfileForm({
  initialData = {},
  onSubmit,
  onCancel,
  loading = false,
}) {
  const [formData, setFormData] = useState({
    bio: initialData?.bio || '',
    phone: initialData?.phone || '',
    location: initialData?.location || '',
    education: initialData?.education || '',
    experience_years: initialData?.experience_years ?? '',
    gender: initialData?.gender || '',
    date_of_birth: initialData?.date_of_birth || '',
  })

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    // Convert experience_years to number if filled
    const payload = {
      ...formData,
      experience_years:
        formData.experience_years !== '' ? Number.parseFloat(formData.experience_years) : null,
      phone: formData.phone || null,
      location: formData.location || null,
      education: formData.education || null,
      gender: formData.gender || null,
      date_of_birth: formData.date_of_birth || null,
      bio: formData.bio || null,
    }
    onSubmit?.(payload)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label htmlFor="phone" className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
            Phone Number
          </label>
          <input
            id="phone"
            name="phone"
            type="tel"
            value={formData.phone}
            onChange={handleChange}
            placeholder="+1 (555) 000-0000"
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-800 outline-none transition focus:border-brand-300 focus:bg-white focus:ring-2 focus:ring-brand-100"
          />
        </div>

        <div>
          <label htmlFor="location" className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
            Location
          </label>
          <input
            id="location"
            name="location"
            type="text"
            value={formData.location}
            onChange={handleChange}
            placeholder="e.g. San Francisco, CA / Remote"
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-800 outline-none transition focus:border-brand-300 focus:bg-white focus:ring-2 focus:ring-brand-100"
          />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label htmlFor="education" className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
            Education / Degree
          </label>
          <input
            id="education"
            name="education"
            type="text"
            value={formData.education}
            onChange={handleChange}
            placeholder="e.g. B.S. in Computer Science"
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-800 outline-none transition focus:border-brand-300 focus:bg-white focus:ring-2 focus:ring-brand-100"
          />
        </div>

        <div>
          <label htmlFor="experience_years" className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
            Experience (Years)
          </label>
          <input
            id="experience_years"
            name="experience_years"
            type="number"
            step="0.5"
            min="0"
            value={formData.experience_years}
            onChange={handleChange}
            placeholder="e.g. 4"
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-800 outline-none transition focus:border-brand-300 focus:bg-white focus:ring-2 focus:ring-brand-100"
          />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label htmlFor="gender" className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
            Gender
          </label>
          <select
            id="gender"
            name="gender"
            value={formData.gender}
            onChange={handleChange}
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-800 outline-none transition focus:border-brand-300 focus:bg-white focus:ring-2 focus:ring-brand-100"
          >
            <option value="">Prefer not to say</option>
            <option value="Female">Female</option>
            <option value="Male">Male</option>
            <option value="Non-binary">Non-binary</option>
            <option value="Other">Other</option>
          </select>
        </div>

        <div>
          <label htmlFor="date_of_birth" className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
            Date of Birth
          </label>
          <input
            id="date_of_birth"
            name="date_of_birth"
            type="date"
            value={formData.date_of_birth}
            onChange={handleChange}
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-800 outline-none transition focus:border-brand-300 focus:bg-white focus:ring-2 focus:ring-brand-100"
          />
        </div>
      </div>

      <div>
        <label htmlFor="bio" className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
          Professional Bio / Summary
        </label>
        <textarea
          id="bio"
          name="bio"
          rows={4}
          value={formData.bio}
          onChange={handleChange}
          placeholder="Describe your background, core technical specialties, and career objectives..."
          className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3.5 text-sm text-slate-800 outline-none transition focus:border-brand-300 focus:bg-white focus:ring-2 focus:ring-brand-100"
        />
      </div>

      <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition"
          >
            Cancel
          </button>
        )}

        <Button type="submit" disabled={loading}>
          {loading ? 'Saving Profile...' : 'Save Profile'}
        </Button>
      </div>
    </form>
  )
}

export default ProfileForm
