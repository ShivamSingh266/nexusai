import { Navigate, Route, Routes } from 'react-router-dom'
import App from '../App'
import { ApplicantLayout } from '../app/layouts/ApplicantLayout'
import { NotFoundPage } from '../pages/NotFoundPage'
import { DashboardPage } from '../pages/applicant/DashboardPage'
import { ProfilePage } from '../pages/applicant/ProfilePage'
import { ResumePage } from '../pages/applicant/ResumePage'
import { SkillGapPage } from '../pages/applicant/SkillGapPage'
import { MarketPage } from '../pages/applicant/MarketPage'
import { RoadmapPage } from '../pages/applicant/RoadmapPage'
import { JobsPage } from '../pages/applicant/JobsPage'
import { InterviewPage } from '../pages/applicant/InterviewPage'
import { CareerWhatIfPage } from '../pages/applicant/CareerWhatIfPage'
import { LoginPage } from '../pages/auth/LoginPage'
import { RegisterPage } from '../pages/auth/RegisterPage'
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
import { ProtectedRoute } from './ProtectedRoute'
import { RoleRoute } from './RoleRoute'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<App />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/applicant" element={<Navigate to="/applicant/dashboard" replace />} />
      <Route path="/hiring" element={<Navigate to="/hiring/dashboard" replace />} />
      <Route path="/government" element={<Navigate to="/government/dashboard" replace />} />

      <Route
        path="/applicant"
        element={
          <ProtectedRoute allowedRoles={['applicant']}>
            <ApplicantLayout />
          </ProtectedRoute>
        }
      >
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="resume" element={<ResumePage />} />
        <Route path="skill-gap" element={<SkillGapPage />} />
        <Route path="market" element={<MarketPage />} />
        <Route path="roadmap" element={<RoadmapPage />} />
        <Route path="jobs" element={<JobsPage />} />
        <Route path="interview" element={<InterviewPage />} />
        <Route path="career-what-if" element={<CareerWhatIfPage />} />
      </Route>

      <Route
        path="/hiring"
        element={
          <RoleRoute allowedRoles={['recruiter']} fallbackPath="/login">
            <ApplicantLayout />
          </RoleRoute>
        }
      >
        <Route path="dashboard" element={<HiringDashboardPage />} />
        <Route path="post-job" element={<PostJobPage />} />
        <Route path="candidate-matching" element={<CandidateMatchingPage />} />
        <Route path="shortlist" element={<ShortlistPage />} />
        <Route path="company-profile" element={<CompanyProfilePage />} />
      </Route>

      <Route
        path="/government"
        element={
          <RoleRoute allowedRoles={['government']} fallbackPath="/login">
            <ApplicantLayout />
          </RoleRoute>
        }
      >
        <Route path="dashboard" element={<GovernmentDashboardPage />} />
        <Route path="skill-demand" element={<SkillDemandPage />} />
        <Route path="course-alignment" element={<CourseAlignmentPage />} />
        <Route path="emerging-skills" element={<EmergingSkillsPage />} />
        <Route path="recommendations" element={<RecommendationsPage />} />
        <Route path="reports" element={<GovernmentReportsPage />} />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
