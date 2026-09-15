import { API_BASE_URL } from '../config/env'

export const api = {
  baseUrl: API_BASE_URL,
  getUrl: (path) => `${API_BASE_URL}${path}`,
}
