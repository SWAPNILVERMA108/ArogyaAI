import api, { unwrap } from './api'
import { tokenStorage } from '../utils/tokenStorage'

export const authService = {
  async register(payload) {
    const data = unwrap(await api.post('/auth/register/', payload))
    tokenStorage.set(data.tokens)
    return data.user
  },
  async login(payload) {
    const data = unwrap(await api.post('/auth/login/', payload))
    tokenStorage.set(data.tokens)
    return data.user
  },
  async logout() {
    const refresh = tokenStorage.getRefresh()
    try {
      if (refresh) await api.post('/auth/logout/', { refresh })
    } finally {
      tokenStorage.clear()
    }
  },
  async getProfile() { return unwrap(await api.get('/auth/profile/')) },
  async updateProfile(payload) { return unwrap(await api.put('/auth/profile/', payload)) },
  // Restores a session from the stored refresh token after a page reload.
  async restoreSession() {
    const refresh = tokenStorage.getRefresh()
    if (!refresh) return null
    const refreshed = unwrap(await api.post('/auth/token/refresh/', { refresh }))
    tokenStorage.set(refreshed)
    return this.getProfile()
  },
}
