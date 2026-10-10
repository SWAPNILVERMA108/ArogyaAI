import MockAdapter from 'axios-mock-adapter'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import api, { setSessionExpiredHandler } from '../services/api'
import { tokenStorage } from '../utils/tokenStorage'

describe('api interceptors', () => {
  let mock
  beforeEach(() => {
    localStorage.clear()
    tokenStorage.clear()
    mock = new MockAdapter(api)
  })

  it('attaches the bearer token', async () => {
    tokenStorage.set({ access: 'abc' })
    mock.onGet('/ping/').reply((config) => [200, { success: true, data: config.headers.Authorization }])
    const response = await api.get('/ping/')
    expect(response.data.data).toBe('Bearer abc')
  })

  it('signs the user out when refresh is impossible', async () => {
    const expired = vi.fn()
    setSessionExpiredHandler(expired)
    mock.onGet('/private/').reply(401, { success: false })
    await expect(api.get('/private/')).rejects.toBeDefined()
    expect(expired).toHaveBeenCalledOnce()
    expect(tokenStorage.getAccess()).toBeNull()
  })

  it('does not try to refresh failed logins', async () => {
    const expired = vi.fn()
    setSessionExpiredHandler(expired)
    tokenStorage.set({ refresh: 'r' })
    mock.onPost('/auth/login/').reply(401, { success: false })
    await expect(api.post('/auth/login/', {})).rejects.toBeDefined()
    expect(expired).not.toHaveBeenCalled()
  })
})
