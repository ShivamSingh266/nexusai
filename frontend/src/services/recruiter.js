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
