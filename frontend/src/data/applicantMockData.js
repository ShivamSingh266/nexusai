export const applicantDashboardStats = [
  { title: 'Career Match', value: '92%', subtitle: 'Strong fit', icon: '🎯', trend: '+8%', variant: 'brand' },
  { title: 'Skill Readiness', value: '84%', subtitle: 'Updated this week', icon: '📈', trend: '+6%', variant: 'success' },
  { title: 'Interview Prep', value: '5 steps', subtitle: '2 due this week', icon: '🗓️', trend: '+2', variant: 'warning' },
  { title: 'Jobs Shortlisted', value: '18', subtitle: 'Across 6 roles', icon: '💼', trend: '+3', variant: 'default' },
]

export const applicantJobs = [
  {
    title: 'Data Analyst',
    company: 'Nexa Labs',
    location: 'Remote',
    salary: '$84k - $96k',
    matchScore: 94,
  },
  {
    title: 'Product Analyst',
    company: 'BrightPath',
    location: 'Bengaluru',
    salary: '$78k - $90k',
    matchScore: 89,
  },
  {
    title: 'AI Operations Specialist',
    company: 'CivicAI',
    location: 'Hyderabad',
    salary: '$90k - $110k',
    matchScore: 86,
  },
]

export const applicantSkills = [
  { skill: 'Python', level: 'Advanced', category: 'Core', selected: true },
  { skill: 'SQL', level: 'Advanced', category: 'Data', selected: true },
  { skill: 'Tableau', level: 'Intermediate', category: 'Visualization', selected: false },
  { skill: 'Machine Learning', level: 'Intermediate', category: 'AI', selected: true },
  { skill: 'Product Thinking', level: 'Advanced', category: 'Strategy', selected: false },
]

export const applicantRoadmap = [
  { label: 'Refine resume', done: true },
  { label: 'Complete SQL certification', done: true },
  { label: 'Practice system design interview', done: false },
  { label: 'Apply to 5 jobs this week', done: false },
]

export const applicantNotifications = [
  { id: 1, title: 'Job match alert', message: 'A new Data Analyst role matches your profile.', time: '2m ago', read: false },
  { id: 2, title: 'Interview reminder', message: 'Your mock interview is scheduled for Saturday.', time: '1h ago', read: false },
  { id: 3, title: 'Skill progress', message: 'You are 16% closer to your target role profile.', time: 'Today', read: true },
]

export const applicantProfile = {
  name: 'Aisha Khan',
  email: 'aisha.khan@example.com',
  role: 'Applicant',
  summary: 'Analyst with a strong interest in AI-enabled workforce intelligence and product analytics.',
}

export const applicantInsights = {
  trend: [42, 45, 49, 51, 56, 60, 62],
  skillGap: [
    { name: 'System design', gap: 24, priority: 'High' },
    { name: 'Cloud basics', gap: 18, priority: 'Medium' },
    { name: 'Stakeholder storytelling', gap: 14, priority: 'Low' },
  ],
}
