import { api } from './api'

export const applicantService = {
  getProfile: () => api.get('/api/v1/profile'),
  createProfile: (profile) => api.post('/api/v1/profile', profile),
  updateProfile: (profile) => api.put('/api/v1/profile', profile),
}

export default applicantService
