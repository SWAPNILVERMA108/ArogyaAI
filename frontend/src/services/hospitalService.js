import api, { unwrap } from './api'

export const hospitalService = {
  nearby: async (params) => unwrap(await api.get('/hospitals/nearby/', { params, timeout: 45000 })),
}
