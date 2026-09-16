export const governmentKpis = [
  { label: 'Active Programs', value: '24', detail: '+4 this quarter' },
  { label: 'Skill Demand', value: '81%', detail: '+12.4% YoY' },
  { label: 'Aligned Courses', value: '64', detail: '18 new this cycle' },
  { label: 'Talent Ready', value: '72%', detail: '+9.2% uplift' },
]

export const skillDemandData = [
  { name: 'AI & ML', demand: 92, growth: 28, sector: 'Digital Services', region: 'National', priority: 'high' },
  { name: 'Cybersecurity', demand: 89, growth: 24, sector: 'Public Security', region: 'South', priority: 'high' },
  { name: 'Data Analytics', demand: 85, growth: 22, sector: 'Policy & Planning', region: 'North', priority: 'high' },
  { name: 'Cloud Computing', demand: 82, growth: 21, sector: 'Technology', region: 'West', priority: 'medium' },
  { name: 'UX Research', demand: 78, growth: 19, sector: 'Product Design', region: 'East', priority: 'medium' },
  { name: 'Project Management', demand: 74, growth: 15, sector: 'Operations', region: 'National', priority: 'low' },
]

export const regionalDemand = [
  { region: 'North', share: 26, demand: 'High' },
  { region: 'South', share: 33, demand: 'Very High' },
  { region: 'East', share: 18, demand: 'Moderate' },
  { region: 'West', share: 23, demand: 'High' },
]

export const trendData = [
  { month: 'Jan', value: 54 },
  { month: 'Feb', value: 58 },
  { month: 'Mar', value: 61 },
  { month: 'Apr', value: 65 },
  { month: 'May', value: 71 },
  { month: 'Jun', value: 77 },
  { month: 'Jul', value: 82 },
]

export const governmentInsights = [
  {
    title: 'AI skill demand is rising faster than most sectors',
    detail: 'The strongest growth is concentrated in digital public services and private enterprises with AI adoption programs.',
  },
  {
    title: 'Course alignment needs stronger project-based learning',
    detail: 'Public programs show better theory coverage than applied labs, especially in AI and cloud programs.',
  },
  {
    title: 'Regional talent readiness is uneven',
    detail: 'Southern and western hubs show higher readiness for emerging roles than eastern clusters.',
  },
]

export const courseAlignmentData = [
  {
    program: 'AI Engineering',
    alignmentLevel: 'High',
    alignment: 94,
    status: 'aligned', // aligned | partial | gap
    marketDemand: 92,
    curriculumScore: 89,
    skills: ['Machine Learning', 'Deep Learning', 'PyTorch', 'Model Deployment'],
    summary: 'High market alignment with high university-industry syllabus match.',
    gap: 'Incorporate real-world production monitoring and LLMOps lab sessions.',
    duration: '16 Weeks',
    institution: 'National Tech Consortium',
  },
  {
    program: 'Data Science',
    alignmentLevel: 'High',
    alignment: 88,
    status: 'aligned',
    marketDemand: 86,
    curriculumScore: 85,
    skills: ['Statistical Inference', 'Python', 'SQL', 'Data Storytelling'],
    summary: 'Strong synergy with business analytics and governance data needs.',
    gap: 'Add modern real-time streaming pipelines (Kafka, Flink).',
    duration: '12 Weeks',
    institution: 'Public University Alliance',
  },
  {
    program: 'Cloud Computing',
    alignmentLevel: 'Medium',
    alignment: 72,
    status: 'partial',
    marketDemand: 82,
    curriculumScore: 68,
    skills: ['Cloud Architecture', 'Terraform', 'Kubernetes', 'CI/CD'],
    summary: 'Moderate alignment with gaps in automated infrastructure and FinOps.',
    gap: 'Expand hands-on multi-cloud migration workshops.',
    duration: '14 Weeks',
    institution: 'Vocational Education Board',
  },
  {
    program: 'Traditional IT',
    alignmentLevel: 'Low',
    alignment: 45,
    status: 'gap',
    marketDemand: 74,
    curriculumScore: 42,
    skills: ['Desktop Support', 'Basic Networking', 'Legacy Scripting'],
    summary: 'Low alignment due to over-emphasis on legacy system administration.',
    gap: 'Transition curriculum towards cloud-native admin, automation, and cybersecurity basics.',
    duration: '8 Weeks',
    institution: 'Regional Skills Academy',
  },
]

export const emergingSkillsData = [
  {
    name: 'Generative AI',
    demand: 94,
    growth: 45,
    priority: 'high',
    sector: 'Software & Technology',
    region: 'National',
    action: 'Accelerate specialised university AI labs and research partnerships',
  },
  {
    name: 'Cybersecurity',
    demand: 89,
    growth: 32,
    priority: 'high',
    sector: 'Defense & Financial Services',
    region: 'South',
    action: 'Expand sponsored cyber-defense apprenticeships and red-team simulations',
  },
  {
    name: 'Cloud Security',
    demand: 84,
    growth: 29,
    priority: 'high',
    sector: 'Enterprise IT & Banking',
    region: 'West',
    action: 'Standardize zero-trust architecture certifications across state agencies',
  },
  {
    name: 'Data Engineering',
    demand: 82,
    growth: 26,
    priority: 'medium',
    sector: 'Analytics & Telecom',
    region: 'North',
    action: 'Modernize big-data infrastructure and distributed computing curricula',
  },
  {
    name: 'Robotics',
    demand: 76,
    growth: 21,
    priority: 'medium',
    sector: 'Advanced Manufacturing',
    region: 'East',
    action: 'Incentivize robotics automation vocational pilots in manufacturing hubs',
  },
]

export const recommendationsData = [
  {
    id: 1,
    title: 'Increase AI training programs',
    priority: 'high',
    region: 'South',
    target: 'Target South region',
    action: 'Partner with universities',
    impact: 'Monitor talent readiness',
    detail:
      'Given that the South region exhibits Very High labour demand with 92% AI & ML intensity, allocate immediate funding to university partnerships to scale certified AI training pipelines.',
    kpis: [
      { label: 'Target Trainees', value: '12,500' },
      { label: 'Institutional Partners', value: '18 Universities' },
      { label: 'Projected Uplift', value: '+14% Readiness' },
    ],
  },
  {
    id: 2,
    title: 'National Cybersecurity Apprenticeships',
    priority: 'high',
    region: 'National',
    target: 'Public Security & Financial Sector',
    action: 'Launch 2-year employer co-sponsored apprenticeship vouchers',
    impact: 'Reduce critical infrastructure vacancy rate by 25%',
    detail:
      'Cybersecurity demand has risen 24% YoY. A public-private apprenticeship voucher program will bridge the practical experience gap.',
    kpis: [
      { label: 'Voucher Allocation', value: '5,000 Seats' },
      { label: 'Participating Firms', value: '85 Employers' },
      { label: 'Readiness Target', value: '88% Placement' },
    ],
  },
  {
    id: 3,
    title: 'Modernize Traditional IT Curricula into Cloud-Native',
    priority: 'medium',
    region: 'North & East',
    target: 'Vocational Institutes',
    action: 'Revise curriculum standards to replace legacy IT with Cloud & DevOps modules',
    impact: 'Prevent structural obsolescence for 20,000+ graduates annually',
    detail:
      'Traditional IT programs currently score 45% alignment. Transitioning these to DevOps, containerization, and basic cloud security improves graduate employability.',
    kpis: [
      { label: 'Institutes Covered', value: '42 Centers' },
      { label: 'Faculty Trained', value: '350 Instructors' },
      { label: 'Target Alignment', value: '>75% within 1 year' },
    ],
  },
]

export const governmentReports = [
  {
    id: 'rep-1',
    title: 'Skill Demand Report',
    type: 'Market Intelligence',
    date: '2026-09-12',
    status: 'Ready',
    metric: '81% Demand Index',
    description: 'Comprehensive analysis of skill shortage indices across digital services, security, and public administration.',
  },
  {
    id: 'rep-2',
    title: 'Regional Demand Report',
    type: 'Regional Outlook',
    date: '2026-09-10',
    status: 'Ready',
    metric: '4 Key Economic Hubs',
    description: 'Geographic distribution of talent demand across North, South, East, and West jurisdictions.',
  },
  {
    id: 'rep-3',
    title: 'Course Alignment Report',
    type: 'Curriculum Audit',
    date: '2026-09-08',
    status: 'Reviewed',
    metric: '64 Aligned Programs',
    description: 'Evaluation of tertiary education course alignment against live hiring signals and skill taxonomy.',
  },
  {
    id: 'rep-4',
    title: 'Emerging Skills Report',
    type: 'Technology Forecast',
    date: '2026-09-05',
    status: 'Ready',
    metric: '5 High-Growth Areas',
    description: 'Early signal detection on rapid-growth competencies including Generative AI, Cloud Defense, and Robotics.',
  },
  {
    id: 'rep-5',
    title: 'Workforce Readiness Report',
    type: 'Readiness Assessment',
    date: '2026-09-01',
    status: 'Draft',
    metric: '72% Talent Ready',
    description: 'Assessment of public-sector candidate pools and alignment with impending infrastructure transformations.',
  },
]
