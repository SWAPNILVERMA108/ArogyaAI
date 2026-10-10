import { useCallback, useState } from 'react'

export function useGeolocation() {
  const [position, setPosition] = useState(null)
  const [error, setError] = useState('')
  const [locating, setLocating] = useState(false)

  const locate = useCallback(() => new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      const message = 'This browser cannot share your location. Enter a city or PIN code instead.'
      setError(message)
      reject(new Error(message))
      return
    }
    setLocating(true)
    setError('')
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const result = { latitude: coords.latitude, longitude: coords.longitude }
        setPosition(result)
        setLocating(false)
        resolve(result)
      },
      () => {
        const message = 'Location permission was denied or unavailable. Enter a city or PIN code instead.'
        setError(message)
        setLocating(false)
        reject(new Error(message))
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 },
    )
  }), [])

  return { position, error, locating, locate }
}
