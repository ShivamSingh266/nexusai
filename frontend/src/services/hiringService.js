import { api } from './api'
import { activeJobs } from '../mocks/hiringMockData'
import { candidateMatchData, jobOptions } from '../mocks/candidateMatchingMockData'
import { shortlistCandidates } from '../mocks/shortlistMockData'
import { companyProfile } from '../mocks/companyProfileMockData'

const buildQuery = (filters = {}) => {
  const params = new URLSearchParams()

  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.set(key, value)
    }
  })

  const query = params.toString()
  return query ? `?${query}` : ''
}

export const hiringService = {
  // Real backend endpoints with graceful mock fallback
  getJobs: async (filters) => {
    try {
      return await api.get(`/api/v1/jobs${buildQuery(filters)}`)
    } catch {
      // Fallback to mock data if backend not reachable
      return { data: activeJobs }
    }
  },

  getJob: async (jobId) => {
    try {
      return await api.get(`/api/v1/jobs/${jobId}`)
    } catch {
      const found = activeJobs.find((j) => String(j.id) === String(jobId))
      return { data: found || activeJobs[0] }
    }
  },

  createJob: async (job) => {
    try {
      return await api.post('/api/v1/jobs', job)
    } catch {
      // Mock creation when offline
      return { data: { id: Date.now(), ...job, status: 'published' } }
    }
  },

  updateJob: (jobId, job) => api.patch(`/api/v1/jobs/${jobId}`, job),
  deleteJob: (jobId) => api.del(`/api/v1/jobs/${jobId}`),

  getCompanyProfile: async () => {
    try {
      return await api.get('/api/v1/recruiter/company')
    } catch {
      return { data: companyProfile }
    }
  },

  createCompanyProfile: (company) => api.post('/api/v1/recruiter/company', company),
  updateCompanyProfile: (company) => api.patch('/api/v1/recruiter/company', company),

  // TODO: Replace mock data when Candidate Matching API is available: GET /api/v1/candidates/matching
  getCandidates: async (jobId) => {
    const candidates = jobId
      ? candidateMatchData.filter((c) => c.jobId === jobId)
      : candidateMatchData
    return Promise.resolve([...candidates])
  },

  getJobOptions: async () => {
    return Promise.resolve([...jobOptions])
  },

  // TODO: Replace mock data when Shortlist API is available: GET /api/v1/shortlist
  getShortlist: async () => {
    return Promise.resolve([...shortlistCandidates])
  },
}

export default hiringService
