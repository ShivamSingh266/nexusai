export function ProfileForm() {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5">
      <h3 className="text-lg font-semibold text-slate-900">Edit profile</h3>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <label className="text-sm text-slate-600">
          <span className="mb-2 block font-medium text-slate-700">Full name</span>
          <input className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 outline-none focus:border-brand-300 focus:ring-2 focus:ring-brand-100" defaultValue="Aisha Khan" />
        </label>

        <label className="text-sm text-slate-600">
          <span className="mb-2 block font-medium text-slate-700">Email</span>
          <input className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 outline-none focus:border-brand-300 focus:ring-2 focus:ring-brand-100" defaultValue="aisha.khan@example.com" />
        </label>
      </div>

      <div className="mt-4">
        <label className="text-sm text-slate-600">
          <span className="mb-2 block font-medium text-slate-700">Summary</span>
          <textarea className="min-h-[120px] w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 outline-none focus:border-brand-300 focus:ring-2 focus:ring-brand-100" defaultValue="Analyst with a strong interest in AI-enabled workforce intelligence and product analytics." />
        </label>
      </div>
    </div>
  )
}
