import api, { unwrap } from './api'

export const patientService = {
  async getMine() {
    try {
      return unwrap(await api.get('/patients/me/'))
    } catch (error) {
      if (error.response?.status === 404) return null // no profile created yet
      throw error
    }
  },
  create: async (payload) => unwrap(await api.post('/patients/', payload)),
  update: async (payload) => unwrap(await api.put('/patients/me/', payload)),
  listAccess: async () => unwrap(await api.get('/patients/access/')),
  grantAccess: async (doctorEmail) => unwrap(await api.post('/patients/access/', { doctor_email: doctorEmail })),
  revokeAccess: async (id) => unwrap(await api.delete(`/patients/access/${id}/`)),
}
