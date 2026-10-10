import api, { unwrap } from './api'

export const healthService = {
  categories: async () => unwrap(await api.get('/health/categories/')),
  tips: async (category) => unwrap(await api.get('/health/tips/', { params: category ? { category } : {} })),
}
