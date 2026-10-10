export const formatDateTime = (value, locale = 'en-IN') =>
  value ? new Date(value).toLocaleString(locale, { dateStyle: 'medium', timeStyle: 'short' }) : ''

export const formatDate = (value, locale = 'en-IN') =>
  value ? new Date(value).toLocaleDateString(locale, { dateStyle: 'medium' }) : ''

export const formatTime = (hhmmss) => (hhmmss ? hhmmss.slice(0, 5) : '')

export const formatBytes = (bytes) =>
  bytes > 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`
