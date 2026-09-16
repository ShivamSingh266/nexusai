export function getRoleHome(role) {
  if (role === 'government') return '/government/dashboard'
  if (role === 'applicant') return '/'
  return '/hiring/dashboard'
}
