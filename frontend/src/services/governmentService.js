import {
  governmentKpis,
  skillDemandData,
  regionalDemand,
  courseAlignmentData,
  emergingSkillsData,
  recommendationsData,
  governmentReports,
} from '../mocks/governmentMockData'

/**
 * Government Service Layer
 * Centralizes data access for all Government Command Center and intelligence pages.
 *
 * NOTE: When backend government intelligence endpoints land in FastAPI,
 * wire them through `api.js` here without redesigning page components.
 */
export const governmentService = {
  // TODO: Replace mock data when Government API is available: GET /api/v1/government/kpis
  getKpis: async () => {
    return Promise.resolve([...governmentKpis])
  },

  // TODO: Replace mock data when Government API is available: GET /api/v1/government/skill-demand
  getSkillDemand: async () => {
    return Promise.resolve([...skillDemandData])
  },

  // TODO: Replace mock data when Government API is available: GET /api/v1/government/regional-demand
  getRegionalDemand: async () => {
    return Promise.resolve([...regionalDemand])
  },

  // TODO: Replace mock data when Government API is available: GET /api/v1/government/course-alignment
  getCourseAlignment: async () => {
    return Promise.resolve([...courseAlignmentData])
  },

  // TODO: Replace mock data when Government API is available: GET /api/v1/government/emerging-skills
  getEmergingSkills: async () => {
    return Promise.resolve([...emergingSkillsData])
  },

  // TODO: Replace mock data when Government API is available: GET /api/v1/government/recommendations
  getRecommendations: async () => {
    return Promise.resolve([...recommendationsData])
  },

  // TODO: Replace mock data when Government API is available: GET /api/v1/government/reports
  getReports: async () => {
    return Promise.resolve([...governmentReports])
  },
}

export default governmentService
