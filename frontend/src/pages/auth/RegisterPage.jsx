import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { getRoleHome } from '../../auth/roleUtils'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '', full_name: '', role: 'applicant' })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }))
  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const user = await register(form)
      navigate(getRoleHome(user.role), { replace: true })
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <h1 className="text-2xl font-bold text-slate-900">Create your NexusAI account</h1>
        <p className="mt-2 text-sm text-slate-600">Register as an applicant or recruiter.</p>
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <label className="block text-sm font-medium text-slate-700">Full name
            <input required minLength="2" value={form.full_name} onChange={(event) => update('full_name', event.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 px-3.5 py-2.5" />
          </label>
          <label className="block text-sm font-medium text-slate-700">Email
            <input required type="email" value={form.email} onChange={(event) => update('email', event.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 px-3.5 py-2.5" />
          </label>
          <label className="block text-sm font-medium text-slate-700">Password
            <input required minLength="8" type="password" value={form.password} onChange={(event) => update('password', event.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 px-3.5 py-2.5" />
          </label>
          <label className="block text-sm font-medium text-slate-700">Account type
            <select value={form.role} onChange={(event) => update('role', event.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 px-3.5 py-2.5">
              <option value="applicant">Applicant</option>
              <option value="recruiter">Recruiter</option>
            </select>
          </label>
          {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
          <button disabled={submitting} className="w-full rounded-xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white disabled:opacity-60">
            {submitting ? 'Creating account...' : 'Create account'}
          </button>
          <p className="text-center text-sm text-slate-600">Already registered? <Link className="font-semibold text-brand-700" to="/login">Sign in</Link></p>
        </form>
      </section>
    </main>
  )
}
