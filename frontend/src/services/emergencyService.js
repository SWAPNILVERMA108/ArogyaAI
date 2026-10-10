import api, { unwrap } from './api'

export const emergencyService = {
  info: async () => unwrap(await api.get('/emergency/info/')),
  listContacts: async () => unwrap(await api.get('/emergency/contacts/')),
  createContact: async (payload) => unwrap(await api.post('/emergency/contacts/', payload)),
  updateContact: async (id, payload) => unwrap(await api.patch(`/emergency/contacts/${id}/`, payload)),
  deleteContact: async (id) => unwrap(await api.delete(`/emergency/contacts/${id}/`)),
  shareLocation: async ({ latitude, longitude, contactId }) =>
    unwrap(await api.post('/emergency/location-share/', {
      latitude, longitude, ...(contactId ? { emergency_contact_id: contactId } : {}),
    })),
}
