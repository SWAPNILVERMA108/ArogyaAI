import api, { unwrap } from './api'

export const medicineService = {
  list: async () => unwrap(await api.get('/medicines/')),
  create: async (payload) => unwrap(await api.post('/medicines/', payload)),
  update: async (id, payload) => unwrap(await api.put(`/medicines/${id}/`, payload)),
  remove: async (id) => unwrap(await api.delete(`/medicines/${id}/`)),
  markTaken: async (id, note = '') => unwrap(await api.post(`/medicines/${id}/taken/`, note ? { note } : {})),
  logs: async (id) => unwrap(await api.get(`/medicines/${id}/logs/`)),
  addReminder: async (id, payload) => unwrap(await api.post(`/medicines/${id}/reminders/`, payload)),
  removeReminder: async (id, reminderId) => unwrap(await api.delete(`/medicines/${id}/reminders/${reminderId}/`)),
}
