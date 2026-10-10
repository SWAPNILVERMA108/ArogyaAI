// Access token lives in memory only. The refresh token is kept in localStorage
// so a user stays signed in after closing the browser; this trades some XSS
// exposure for usability on shared/low-connectivity devices.
const REFRESH_KEY = 'arogyaai.refresh'
let accessToken = null

export const tokenStorage = {
  getAccess: () => accessToken,
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set({ access, refresh }) {
    if (access) accessToken = access
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
  },
  clear() {
    accessToken = null
    localStorage.removeItem(REFRESH_KEY)
  },
}
