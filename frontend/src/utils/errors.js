export function getErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  if (!error) return fallback
  if (error.code === 'ERR_NETWORK') return 'Cannot reach the server. Check your internet connection.'
  const apiError = error.response?.data?.error
  if (apiError?.details && typeof apiError.details === 'object' && !Array.isArray(apiError.details)) {
    const first = Object.entries(apiError.details).find(([key]) => key !== 'detail')
    if (first) {
      const [field, value] = first
      const text = Array.isArray(value) ? value[0] : String(value)
      return field === 'non_field_errors' ? text : `${field}: ${text}`
    }
  }
  return apiError?.message || error.message || fallback
}

// Field-level errors from the API, keyed by field name, for react-hook-form.
export function getFieldErrors(error) {
  const details = error.response?.data?.error?.details
  if (!details || typeof details !== 'object') return {}
  return Object.fromEntries(
    Object.entries(details).map(([field, value]) => [field, Array.isArray(value) ? value[0] : String(value)]),
  )
}
