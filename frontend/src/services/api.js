import { API_BASE_URL } from '../config/env'

const API_PREFIX = '/api/v1'
const TOKEN_KEY = 'nexusai_access_token'

export class ApiError extends Error {
  constructor(message, { status, detail, response } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.response = response
  }
}

const getAccessToken = () => localStorage.getItem(TOKEN_KEY)

const buildUrl = (path, query) => {
  let normalizedPath = path.startsWith('/') ? path : `/${path}`
  if (!normalizedPath.startsWith(API_PREFIX) && !normalizedPath.startsWith('http')) {
    normalizedPath = `${API_PREFIX}${normalizedPath}`
  }
  const url = new URL(`${API_BASE_URL}${normalizedPath}`)

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value))
      }
    })
  }

  return url.toString()
}

const getErrorDetail = (responseBody, status) => {
  if (typeof responseBody?.detail === 'string') return responseBody.detail
  if (Array.isArray(responseBody?.detail)) {
    return responseBody.detail.map((item) => item.msg || item.detail || JSON.stringify(item)).join(', ')
  }
  return `Request failed with status ${status}.`
}

export const request = async (path, options = {}) => {
  const { accessToken, body, headers: customHeaders, query, ...fetchOptions } = options
  const token = accessToken || getAccessToken()
  const headers = new Headers(customHeaders)
  const isFormData = body instanceof FormData

  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (body !== undefined && !isFormData && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const requestBody = body !== undefined && !isFormData && typeof body !== 'string'
    ? JSON.stringify(body)
    : body

  let response
  try {
    response = await fetch(buildUrl(path, query), { ...fetchOptions, body: requestBody, headers })
  } catch {
    throw new ApiError('Unable to reach the NexusAI server. Check your connection and try again.', { status: 0 })
  }

  const contentType = response.headers.get('content-type') || ''
  const responseBody = response.status === 204
    ? null
    : contentType.includes('application/json')
      ? await response.json()
      : await response.text()

  if (!response.ok) {
    const detail = getErrorDetail(responseBody, response.status)
    throw new ApiError(detail, { status: response.status, detail, response: responseBody })
  }

  return responseBody
}

export const api = {
  baseUrl: API_BASE_URL,
  getUrl: (path) => `${API_BASE_URL}${API_PREFIX}${path.startsWith('/') ? path : `/${path}`}`,
  request,
  get: (path, options = {}) => request(path, { ...options, method: 'GET' }),
  post: (path, bodyOrOptions, options = {}) => {
    const isOptions = bodyOrOptions && !Array.isArray(bodyOrOptions) && typeof bodyOrOptions === 'object' && ('body' in bodyOrOptions || 'accessToken' in bodyOrOptions)
    if (isOptions && Object.keys(options).length === 0) {
      return request(path, { ...bodyOrOptions, method: 'POST' })
    }
    return request(path, { ...options, body: bodyOrOptions, method: 'POST' })
  },
  put: (path, bodyOrOptions, options = {}) => {
    const isOptions = bodyOrOptions && !Array.isArray(bodyOrOptions) && typeof bodyOrOptions === 'object' && ('body' in bodyOrOptions || 'accessToken' in bodyOrOptions)
    if (isOptions && Object.keys(options).length === 0) {
      return request(path, { ...bodyOrOptions, method: 'PUT' })
    }
    return request(path, { ...options, body: bodyOrOptions, method: 'PUT' })
  },
  patch: (path, bodyOrOptions, options = {}) => {
    const isOptions = bodyOrOptions && !Array.isArray(bodyOrOptions) && typeof bodyOrOptions === 'object' && ('body' in bodyOrOptions || 'accessToken' in bodyOrOptions)
    if (isOptions && Object.keys(options).length === 0) {
      return request(path, { ...bodyOrOptions, method: 'PATCH' })
    }
    return request(path, { ...options, body: bodyOrOptions, method: 'PATCH' })
  },
  delete: (path, options = {}) => request(path, { ...options, method: 'DELETE' }),
  del: (path, options = {}) => request(path, { ...options, method: 'DELETE' }),
}

export default api
