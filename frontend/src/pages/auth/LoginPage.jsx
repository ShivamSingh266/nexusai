import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { getRoleHome } from '../../auth/roleUtils'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }))
  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const user = await login(form)
      navigate(location.state?.from?.pathname || getRoleHome(user.role), { replace: true })
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthPage title="Sign in to NexusAI" subtitle="Use your NexusAI account to continue.">
      <form onSubmit={handleSubmit} className="space-y-4">
        <AuthInput label="Email" type="email" value={form.email} onChange={(value) => update('email', value)} />
        <AuthInput label="Password" type="password" value={form.password} onChange={(value) => update('password', value)} />
        {error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        <button disabled={submitting} className="w-full rounded-xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white disabled:opacity-60">
          {submitting ? 'Signing in...' : 'Sign in'}
        </button>
        <p className="text-center text-sm text-slate-600">
          New to NexusAI? <Link className="font-semibold text-brand-700" to="/register">Create an account</Link>
        </p>
      </form>
    </AuthPage>
  )
}

function AuthInput({ label, type, value, onChange }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      <input required type={type} value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 px-3.5 py-2.5" />
    </label>
  )
}

function AuthPage({ title, subtitle, children }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        <p className="mt-2 text-sm text-slate-600">{subtitle}</p>
        <div className="mt-6">{children}</div>
      </section>
    </main>
  )
}
