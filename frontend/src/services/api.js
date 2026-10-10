import axios from 'axios'
import { tokenStorage } from '../utils/tokenStorage'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const api = axios.create({ baseURL: API_BASE_URL, timeout: 60000 })

// A bare client without interceptors, used only for token refresh.
const refreshClient = axios.create({ baseURL: API_BASE_URL, timeout: 20000 })

let onSessionExpired = () => {}
export const setSessionExpiredHandler = (handler) => { onSessionExpired = handler }

api.interceptors.request.use((config) => {
  const token = tokenStorage.getAccess()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshPromise = null

async function refreshAccessToken() {
  const refresh = tokenStorage.getRefresh()
  if (!refresh) throw new Error('No refresh token')
  const { data } = await refreshClient.post('/auth/token/refresh/', { refresh })
  tokenStorage.set(data.data) // ROTATE_REFRESH_TOKENS: a new refresh token may be returned
  return data.data.access
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const isAuthCall = original?.url?.includes('/auth/login/') || original?.url?.includes('/auth/register/')
    if (error.response?.status !== 401 || !original || original._retried || isAuthCall) {
      return Promise.reject(error)
    }
    original._retried = true
    try {
      // Share one refresh across concurrent 401s.
      refreshPromise ??= refreshAccessToken().finally(() => { refreshPromise = null })
      const access = await refreshPromise
      original.headers.Authorization = `Bearer ${access}`
      return api(original)
    } catch {
      tokenStorage.clear()
      onSessionExpired()
      return Promise.reject(error)
    }
  },
)

// Every backend success response is { success, data, message }.
export const unwrap = (response) => response.data.data

export default api
