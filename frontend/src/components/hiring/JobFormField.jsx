export function JobFormField({
  label,
  id,
  name,
  type = 'text',
  value,
  onChange,
  placeholder,
  error,
  options = [],
  as = 'input',
  children,
}) {
  const sharedClassName = `mt-2 w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-slate-700 shadow-sm transition-colors placeholder:text-slate-400 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100 ${
    error ? 'border-red-300 bg-red-50' : 'border-slate-200'
  }`

  const inputContent =
    as === 'select' ? (
      <select id={id} name={name} value={value} onChange={onChange} className={sharedClassName}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    ) : as === 'textarea' ? (
      <textarea
        id={id}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        rows={6}
        className={`${sharedClassName} resize-none`}
      />
    ) : (
      <input
        id={id}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={sharedClassName}
      />
    )

  return (
    <label htmlFor={id} className="block text-sm font-medium text-slate-700">
      {label}
      {inputContent}
      {error ? <span className="mt-1 inline-block text-xs text-red-600">{error}</span> : null}
      {children}
    </label>
  )
}
