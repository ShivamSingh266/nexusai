export function ResumePage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-700">Resume</p>
        <h2 className="mt-2 text-3xl font-bold text-slate-900">Resume & profile upload</h2>
      </div>

      <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-3xl shadow-sm">📄</div>
        <h3 className="text-xl font-semibold text-slate-900">Upload your resume</h3>
        <p className="mt-2 text-sm text-slate-500">Add a resume to enable automatic skill extraction and better job matching.</p>
        <button type="button" className="mt-5 rounded-full bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700">
          Choose file
        </button>
      </div>
    </div>
  )
}
