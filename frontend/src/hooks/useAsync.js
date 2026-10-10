import { useCallback, useEffect, useRef, useState } from 'react'
import { getErrorMessage } from '../utils/errors'

// Loads data on mount (and on reload()), tracking loading and error state.
export function useAsync(loader, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const loaderRef = useRef(loader)
  loaderRef.current = loader

  const reload = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setData(await loaderRef.current())
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { reload() }, deps)
  return { data, setData, loading, error, reload }
}
