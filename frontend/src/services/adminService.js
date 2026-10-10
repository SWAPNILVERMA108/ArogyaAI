import api, { unwrap } from './api'

export const adminService = {
  stats: async () => unwrap(await api.get('/admin/stats/')),
  users: async (params) => unwrap(await api.get('/admin/users/', { params })),
  updateUser: async (id, payload) => unwrap(await api.patch(`/admin/users/${id}/`, payload)),
}

export const doctorService = {
  patients: async () => unwrap(await api.get('/doctor/patients/')),
  patient: async (id) => unwrap(await api.get(`/doctor/patients/${id}/`)),
}
