import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { AuthLayout } from '../../app/layouts/AuthLayout'
import { auth, getDefaultDashboardForRole } from '../../services/auth'

const roleOptions = ['applicant', 'recruiter', 'government']

export function RegisterPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'applicant',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const user = auth.getUser()

  if (auth.isAuthenticated() && user) {
    return <Navigate to={getDefaultDashboardForRole(user.role)} replace />
  }

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const result = await auth.register(form)
      const nextUser = result?.data || auth.getUser()
      const redirectTo = getDefaultDashboardForRole(nextUser?.role)

      navigate(redirectTo, { replace: true })
    } catch (submissionError) {
      setError(submissionError.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout title="Create account" subtitle="Join NexusAI and start exploring opportunities">
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label htmlFor="full_name" className="mb-2 block text-sm font-medium text-slate-700">
            Full name
          </label>
          <input
            id="full_name"
            name="full_name"
            type="text"
            required
            value={form.full_name}
            onChange={handleChange}
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-800 outline-none transition focus:border-brand-300 focus:bg-white focus:ring-2 focus:ring-brand-100"
            placeholder="Jane Doe"
          />
        </div>

        <div>
          <label htmlFor="email" className="mb-2 block text-sm font-medium text-slate-700">
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            value={form.email}
            onChange={handleChange}
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-800 outline-none transition focus:border-brand-300 focus:bg-white focus:ring-2 focus:ring-brand-100"
            placeholder="jane@example.com"
          />
        </div>

        <div>
          <label htmlFor="password" className="mb-2 block text-sm font-medium text-slate-700">
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            required
            value={form.password}
            onChange={handleChange}
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-800 outline-none transition focus:border-brand-300 focus:bg-white focus:ring-2 focus:ring-brand-100"
            placeholder="Create a password"
          />
        </div>

        <div>
          <label htmlFor="role" className="mb-2 block text-sm font-medium text-slate-700">
            Role
          </label>
          <select
            id="role"
            name="role"
            value={form.role}
            onChange={handleChange}
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-800 outline-none transition focus:border-brand-300 focus:bg-white focus:ring-2 focus:ring-brand-100"
          >
            {roleOptions.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-brand-400"
        >
          {loading ? 'Creating account...' : 'Create account'}
        </button>

        <div className="text-center text-sm text-slate-600">
          Already have an account?{' '}
          <Link to="/login" className="font-semibold text-brand-700 hover:text-brand-800">
            Sign in
          </Link>
        </div>
      </form>
    </AuthLayout>
  )
}
