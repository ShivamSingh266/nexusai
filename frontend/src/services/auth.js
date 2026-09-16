import { API_BASE_URL } from '../config/env'

const TOKEN_KEY = 'nexusai_access_token'
const REFRESH_TOKEN_KEY = 'nexusai_refresh_token'
const USER_KEY = 'nexusai_user'

export const roleRedirectMap = {
  applicant: '/applicant/dashboard',
  recruiter: '/hiring/dashboard',
  government: '/government/dashboard',
  admin: '/government/dashboard',
}

export const getDefaultDashboardForRole = (role) => roleRedirectMap[role] || '/'

export const getAccessToken = () => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) return token
  try {
    const stored = JSON.parse(localStorage.getItem('nexusai.auth'))
    return stored?.access_token || null
  } catch {
    return null
  }
}

export const getRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY)

export const getStoredUser = () => {
  const storedUser = localStorage.getItem(USER_KEY)

  if (!storedUser) {
    return null
  }

  try {
    return JSON.parse(storedUser)
  } catch {
    return null
  }
}

export const getAuthHeaders = () => {
  const token = getAccessToken()

  return token
    ? {
        Authorization: `Bearer ${token}`,
      }
    : {}
}

export const saveSession = (data) => {
  if (data?.access_token) {
    localStorage.setItem(TOKEN_KEY, data.access_token)
    localStorage.setItem('nexusai.auth', JSON.stringify({
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      token_type: data.token_type || 'bearer',
    }))
  }

  if (data?.refresh_token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token)
  }

  if (data?.data) {
    localStorage.setItem(USER_KEY, JSON.stringify(data.data))
  }

  if (data?.user) {
    localStorage.setItem(USER_KEY, JSON.stringify(data.user))
  }

  return data
}

export const clearSession = () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem('nexusai.auth')
}

const parseError = (data, fallbackMessage) => {
  if (data?.detail) return data.detail
  if (data?.message) return data.message
  if (data?.error) return data.error
  return fallbackMessage
}

export const auth = {
  isAuthenticated: () => Boolean(getAccessToken()),

  getUser: () => getStoredUser(),

  login: async (email, password) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      throw new Error(parseError(data, 'Login failed'))
    }

    return saveSession(data)
  },

  register: async ({ full_name, email, password, role }) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ full_name, email, password, role }),
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      throw new Error(parseError(data, 'Registration failed'))
    }

    return saveSession(data)
  },

  getCurrentUser: async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/users/me`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      throw new Error(parseError(data, 'Unable to load user profile'))
    }

    const user = data?.data || data?.user || data

    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    }

    return user
  },

  logout: () => {
    clearSession()
    return true
  },
}

export const login = (credentials) => auth.login(credentials.email || credentials.username, credentials.password)
export const register = (details) => auth.register(details)
export const getCurrentUser = () => auth.getCurrentUser()
export const logout = () => auth.logout()

export default auth
