import api, { unwrap } from './api'

// Error bodies for blob responses arrive as Blobs; convert them so the
// shared error helper can read the API message.
async function normaliseBlobError(error) {
  const data = error.response?.data
  if (data instanceof Blob) {
    try { error.response.data = JSON.parse(await data.text()) } catch { /* keep as is */ }
  }
  throw error
}

export const voiceService = {
  async transcribe(audioBlob, language) {
    const form = new FormData()
    // Strip codec parameters (e.g. "audio/webm;codecs=opus") the API does not whitelist.
    const type = (audioBlob.type || 'audio/webm').split(';')[0]
    const extension = type.split('/')[1] || 'webm'
    form.append('audio', new File([audioBlob], `speech.${extension}`, { type }))
    form.append('language', language)
    form.append('consent_to_cloud_processing', 'true')
    return unwrap(await api.post('/voice/transcribe/', form, { timeout: 120000 }))
  },
  async speak(text, language) {
    try {
      const response = await api.post('/voice/speak/', { text, language }, { responseType: 'blob', timeout: 120000 })
      return response.data
    } catch (error) {
      return normaliseBlobError(error)
    }
  },
}
