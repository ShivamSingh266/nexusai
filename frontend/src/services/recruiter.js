import { api } from './api'

export const getCompany = (accessToken) => api.get('/recruiter/company', { accessToken })
export const createCompany = (payload, accessToken) => api.post('/recruiter/company', payload, { accessToken })
export const updateCompany = (payload, accessToken) => api.patch('/recruiter/company', payload, { accessToken })

export const listJobs = (accessToken, query = {}) => api.get('/jobs', { accessToken, query })
export const createJob = (payload, accessToken) => api.post('/jobs', payload, { accessToken })
export const updateJob = (jobId, payload, accessToken) => api.patch(`/jobs/${jobId}`, payload, { accessToken })
export const deleteJob = (jobId, accessToken) => api.delete(`/jobs/${jobId}`, { accessToken })

export const listJobSkills = (jobId, accessToken) => api.get(`/jobs/${jobId}/skills`, { accessToken })
export const createJobSkills = (jobId, skills, accessToken) => (
  api.post(`/jobs/${jobId}/skills/bulk`, { skills }, { accessToken })
)

export const searchTaxonomy = (query, accessToken) => api.get('/taxonomy/skills/search', {
  accessToken,
  query: { q: query, limit: 10 },
})

export const getVersions = (accessToken) => api.get('/meta/versions', { accessToken })

export const getCandidateMatches = (jobId, accessToken) => (
  api.get(`/matching/candidates/${jobId}`, { accessToken })
)

export const listShortlists = (accessToken, query = {}) => (
  api.get('/shortlists', { accessToken, query })
)

export const listShortlistsForJob = (jobId, accessToken) => (
  api.get(`/shortlists/job/${jobId}`, { accessToken })
)

export const createShortlist = (payload, accessToken) => (
  api.post('/shortlists', payload, { accessToken })
)

export const updateShortlist = (shortlistId, payload, accessToken) => (
  api.patch(`/shortlists/${shortlistId}`, payload, { accessToken })
)

export const deleteShortlist = (shortlistId, accessToken) => (
  api.delete(`/shortlists/${shortlistId}`, { accessToken })
)

export const deleteShortlistCandidate = (jobId, candidateId, accessToken) => (
  api.delete(`/shortlists/job/${jobId}/candidate/${candidateId}`, { accessToken })
)
