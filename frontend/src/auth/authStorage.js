const STORAGE_KEY = 'nexusai.auth'

export const authStorage = {
  get() {
    try {
      const value = window.localStorage.getItem(STORAGE_KEY)
      return value ? JSON.parse(value) : null
    } catch {
      return null
    }
  },
  set(auth) {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(auth))
  },
  clear() {
    window.localStorage.removeItem(STORAGE_KEY)
  },
}
