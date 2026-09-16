import {
  BarChart3,
  BriefcaseBusiness,
  Building2,
  CalendarRange,
  FileText,
  FolderKanban,
  LayoutDashboard,
  Map,
  MessageSquareText,
  Route,
  Search,
  Target,
  TrendingUp,
  UserRound,
  Users,
  BookOpen,
} from 'lucide-react'

export const applicantNavigation = [
  { id: 'dashboard', title: 'Dashboard', path: '/applicant/dashboard', icon: LayoutDashboard },
  { id: 'profile', title: 'Profile', path: '/applicant/profile', icon: UserRound },
  { id: 'resume', title: 'Resume', path: '/applicant/resume', icon: FileText },
  { id: 'skill-gap', title: 'Skill Gap', path: '/applicant/skill-gap', icon: Target },
  { id: 'market', title: 'Market', path: '/applicant/market', icon: TrendingUp },
  { id: 'roadmap', title: 'Roadmap', path: '/applicant/roadmap', icon: Route },
  { id: 'jobs', title: 'Jobs', path: '/applicant/jobs', icon: BriefcaseBusiness },
  { id: 'interview', title: 'Interview', path: '/applicant/interview', icon: CalendarRange },
  { id: 'career-what-if', title: 'Career What-If', path: '/applicant/career-what-if', icon: Map },
]

export const recruiterNavigation = [
  { id: 'dashboard', title: 'Dashboard', path: '/hiring/dashboard', icon: LayoutDashboard },
  { id: 'post-job', title: 'Post Job', path: '/hiring/post-job', icon: BriefcaseBusiness },
  { id: 'candidate-matching', title: 'Candidate Matching', path: '/hiring/candidate-matching', icon: Users },
  { id: 'shortlist', title: 'Shortlist', path: '/hiring/shortlist', icon: FolderKanban },
  { id: 'company-profile', title: 'Company Profile', path: '/hiring/company-profile', icon: Building2 },
]

export const governmentNavigation = [
  { id: 'dashboard', title: 'Dashboard', path: '/government/dashboard', icon: LayoutDashboard },
  { id: 'skill-demand', title: 'Skill Demand', path: '/government/skill-demand', icon: BarChart3 },
  { id: 'course-alignment', title: 'Course Alignment', path: '/government/course-alignment', icon: BookOpen },
  { id: 'emerging-skills', title: 'Emerging Skills', path: '/government/emerging-skills', icon: TrendingUp },
  { id: 'recommendations', title: 'Recommendations', path: '/government/recommendations', icon: MessageSquareText },
  { id: 'reports', title: 'Reports', path: '/government/reports', icon: Search },
]

export const navigationByRole = {
  applicant: applicantNavigation,
  recruiter: recruiterNavigation,
  government: governmentNavigation,
  admin: governmentNavigation,
}

export const roleLabelMap = {
  applicant: 'Applicant',
  recruiter: 'Recruiter',
  government: 'Government',
  admin: 'Admin',
}
