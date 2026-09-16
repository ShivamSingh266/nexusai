import { API_BASE_URL } from '../config/env'

const API_PREFIX = '/api/v1'

export class ApiError extends Error {
  constructor(message, { status, detail, response } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.response = response
  }
}

const buildUrl = (path, query) => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const url = new URL(`${API_BASE_URL}${API_PREFIX}${normalizedPath}`)

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

const request = async (path, options = {}) => {
  const { accessToken, body, headers: customHeaders, query, ...fetchOptions } = options
  const headers = new Headers(customHeaders)
  const isFormData = body instanceof FormData

  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
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
  post: (path, body, options = {}) => request(path, { ...options, body, method: 'POST' }),
  put: (path, body, options = {}) => request(path, { ...options, body, method: 'PUT' }),
  patch: (path, body, options = {}) => request(path, { ...options, body, method: 'PATCH' }),
  delete: (path, options = {}) => request(path, { ...options, method: 'DELETE' }),
}
