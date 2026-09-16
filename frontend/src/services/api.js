import { API_BASE_URL } from '../config/env'

const TOKEN_KEY = 'nexusai_access_token'

const getAccessToken = () => localStorage.getItem(TOKEN_KEY)

const request = async (path, options = {}) => {
  const token = getAccessToken()

  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      data?.detail ||
      data?.message ||
      data?.error ||
      `Request failed with status ${response.status}`

    throw new Error(message)
  }

  return data
}

export const api = {
  baseUrl: API_BASE_URL,
  getUrl: (path) => `${API_BASE_URL}${path}`,
  get: (path) => request(path),
  post: (path, body) =>
    request(path, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  put: (path, body) =>
    request(path, {
      method: 'PUT',
      body: JSON.stringify(body),
    }),
  patch: (path, body) =>
    request(path, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  del: (path) =>
    request(path, {
      method: 'DELETE',
    }),
}
