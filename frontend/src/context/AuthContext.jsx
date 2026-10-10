import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { setSessionExpiredHandler } from '../services/api'
import { authService } from '../services/authService'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [initialising, setInitialising] = useState(true)

  useEffect(() => {
    setSessionExpiredHandler(() => setUser(null))
    let cancelled = false
    authService.restoreSession()
      .then((restored) => { if (!cancelled) setUser(restored) })
      .catch(() => { if (!cancelled) setUser(null) })
      .finally(() => { if (!cancelled) setInitialising(false) })
    return () => { cancelled = true }
  }, [])

  const login = useCallback(async (credentials) => {
    const signedIn = await authService.login(credentials)
    setUser(signedIn)
    return signedIn
  }, [])

  const register = useCallback(async (payload) => {
    const created = await authService.register(payload)
    setUser(created)
    return created
  }, [])

  const logout = useCallback(async () => {
    try { await authService.logout() } finally { setUser(null) }
  }, [])

  const value = useMemo(
    () => ({ user, setUser, initialising, login, register, logout, isAuthenticated: Boolean(user) }),
    [user, initialising, login, register, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
