import { useCallback, useEffect, useMemo, useState } from 'react'
import { authStorage } from './authStorage'
import { ApiError } from '../services/api'
import * as authService from '../services/auth'
import { AuthContext } from './AuthContext'

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(() => authStorage.get())
  const [currentUser, setCurrentUser] = useState(null)
  const [loading, setLoading] = useState(() => Boolean(auth?.access_token))

  const clearAuth = useCallback(() => {
    authStorage.clear()
    setAuth(null)
    setCurrentUser(null)
  }, [])

  const loadCurrentUser = useCallback(async (accessToken = auth?.access_token) => {
    if (!accessToken) {
      return null
    }
    setLoading(true)
    try {
      const response = await authService.getCurrentUser(accessToken)
      setCurrentUser(response.data)
      return response.data
    } catch (error) {
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) clearAuth()
      throw error
    } finally {
      setLoading(false)
    }
  }, [auth?.access_token, clearAuth])

  useEffect(() => {
    if (!auth?.access_token) return
    Promise.resolve().then(() => loadCurrentUser()).catch(() => {})
  }, [auth?.access_token, loadCurrentUser])

  const completeAuthentication = useCallback(async (response) => {
    const nextAuth = {
      access_token: response.access_token,
      refresh_token: response.refresh_token,
      token_type: response.token_type,
    }
    authStorage.set(nextAuth)
    setAuth(nextAuth)
    return loadCurrentUser(nextAuth.access_token)
  }, [loadCurrentUser])

  const login = useCallback(async (credentials) => completeAuthentication(await authService.login(credentials)), [completeAuthentication])
  const register = useCallback(async (details) => completeAuthentication(await authService.register(details)), [completeAuthentication])
  const logout = useCallback(() => {
    authService.logout()
    clearAuth()
  }, [clearAuth])

  const value = useMemo(() => ({
    accessToken: auth?.access_token || null,
    currentUser,
    loading,
    login,
    register,
    logout,
    loadCurrentUser,
  }), [auth?.access_token, currentUser, loadCurrentUser, loading, login, logout, register])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
