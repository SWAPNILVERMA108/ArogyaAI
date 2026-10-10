import api, { unwrap } from './api'

export const reportService = {
  list: async () => unwrap(await api.get('/reports/upload/')),
  upload: async (file) => {
    const form = new FormData()
    form.append('file', file)
    return unwrap(await api.post('/reports/upload/', form, { timeout: 120000 }))
  },
  process: async (id) => unwrap(await api.post(`/reports/${id}/process/`, null, { timeout: 180000 })),
  remove: async (id) => unwrap(await api.delete(`/reports/${id}/`)),
}
