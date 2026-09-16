import { Link, useLocation } from 'react-router-dom'

const LABELS = {
  '/': 'Home',
  '/login': 'Login',
  '/register': 'Register',
  '/applicant': 'Applicant',
  '/applicant/dashboard': 'Applicant Dashboard',
  '/applicant/profile': 'Profile',
  '/applicant/resume': 'Resume',
  '/applicant/skill-gap': 'Skill Gap',
  '/applicant/market': 'Market',
  '/applicant/roadmap': 'Roadmap',
  '/applicant/jobs': 'Jobs',
  '/applicant/interview': 'Interview',
  '/applicant/career-what-if': 'Career What-If',
  '/hiring': 'Hiring',
  '/hiring/dashboard': 'Hiring Dashboard',
  '/hiring/post-job': 'Post a Job',
  '/hiring/candidate-matching': 'Candidate Matching',
  '/hiring/shortlist': 'Shortlist',
  '/hiring/company-profile': 'Company Profile',
  '/government': 'Government',
  '/government/dashboard': 'Government Dashboard',
  '/government/skill-demand': 'Skill Demand',
  '/government/course-alignment': 'Course Alignment',
  '/government/emerging-skills': 'Emerging Skills',
  '/government/recommendations': 'Recommendations',
  '/government/reports': 'Reports',
}

export function Breadcrumbs() {
  const location = useLocation()
  const segments = location.pathname.split('/').filter(Boolean)

  const crumbs = segments.map((segment, index) => {
    const path = `/${segments.slice(0, index + 1).join('/')}`
    return {
      label: LABELS[path] || segment.replace(/-/g, ' '),
      path,
    }
  })

  if (!crumbs.length) {
    return null
  }

  return (
    <nav className="flex flex-wrap items-center gap-2 text-sm text-slate-500">
      <Link to="/" className="font-medium text-slate-600 hover:text-slate-900">
        Home
      </Link>

      {crumbs.map((crumb, index) => (
        <div key={crumb.path} className="flex items-center gap-2">
          <span>/</span>
          {index === crumbs.length - 1 ? (
            <span className="font-medium text-slate-800">{crumb.label}</span>
          ) : (
            <Link to={crumb.path} className="hover:text-slate-900">
              {crumb.label}
            </Link>
          )}
        </div>
      ))}
    </nav>
  )
}
