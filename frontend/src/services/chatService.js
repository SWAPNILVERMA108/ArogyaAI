import api, { unwrap } from './api'

export const chatService = {
  sendMessage: async ({ message, conversationId }) =>
    unwrap(await api.post('/chat/message/', { message, ...(conversationId ? { conversation_id: conversationId } : {}) })),
  listConversations: async () => unwrap(await api.get('/chat/conversations/')),
  getConversation: async (id) => unwrap(await api.get(`/chat/conversations/${id}/`)),
  deleteConversation: async (id) => unwrap(await api.delete(`/chat/conversations/${id}/`)),
  clearMessages: async (id) => unwrap(await api.delete(`/chat/conversations/${id}/messages/`)),
}
