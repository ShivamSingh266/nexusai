import { Navigate, Route, Routes } from 'react-router-dom'
import App from '../App'
import { HiringDashboardPage } from '../pages/hiring/HiringDashboardPage'
import { PostJobPage } from '../pages/hiring/PostJobPage'
import { CandidateMatchingPage } from '../pages/hiring/CandidateMatchingPage'
import { ShortlistPage } from '../pages/hiring/ShortlistPage'
import { CompanyProfilePage } from '../pages/hiring/CompanyProfilePage'
import { GovernmentDashboardPage } from '../pages/government/GovernmentDashboardPage'
import { SkillDemandPage } from '../pages/government/SkillDemandPage'
import { CourseAlignmentPage } from '../pages/government/CourseAlignmentPage'
import { EmergingSkillsPage } from '../pages/government/EmergingSkillsPage'
import { RecommendationsPage } from '../pages/government/RecommendationsPage'
import { GovernmentReportsPage } from '../pages/government/GovernmentReportsPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<App />} />
      <Route path="/hiring/dashboard" element={<HiringDashboardPage />} />
      <Route path="/hiring/post-job" element={<PostJobPage />} />
      <Route path="/hiring/candidate-matching" element={<CandidateMatchingPage />} />
      <Route path="/hiring/shortlist" element={<ShortlistPage />} />
      <Route path="/hiring/company-profile" element={<CompanyProfilePage />} />
      <Route path="/government/dashboard" element={<GovernmentDashboardPage />} />
      <Route path="/government/skill-demand" element={<SkillDemandPage />} />
      <Route path="/government/course-alignment" element={<CourseAlignmentPage />} />
      <Route path="/government/emerging-skills" element={<EmergingSkillsPage />} />
      <Route path="/government/recommendations" element={<RecommendationsPage />} />
      <Route path="/government/reports" element={<GovernmentReportsPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
