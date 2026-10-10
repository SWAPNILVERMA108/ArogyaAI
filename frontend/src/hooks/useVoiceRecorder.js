import { useCallback, useEffect, useRef, useState } from 'react'

const MAX_SECONDS = 60

export function useVoiceRecorder() {
  const [recording, setRecording] = useState(false)
  const [error, setError] = useState('')
  const recorderRef = useRef(null)
  const chunksRef = useRef([])
  const timerRef = useRef(null)
  const resolveRef = useRef(null)

  const supported = typeof window !== 'undefined' && Boolean(navigator.mediaDevices?.getUserMedia) && 'MediaRecorder' in window

  const start = useCallback(async () => {
    setError('')
    if (!supported) {
      setError('Voice recording is not supported in this browser.')
      return false
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      chunksRef.current = []
      recorder.ondataavailable = (event) => { if (event.data.size) chunksRef.current.push(event.data) }
      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop())
        clearTimeout(timerRef.current)
        setRecording(false)
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' })
        resolveRef.current?.(blob)
        resolveRef.current = null
      }
      recorder.start()
      recorderRef.current = recorder
      setRecording(true)
      timerRef.current = setTimeout(() => recorder.state === 'recording' && recorder.stop(), MAX_SECONDS * 1000)
      return true
    } catch {
      setError('Microphone access was denied or is unavailable.')
      return false
    }
  }, [supported])

  // Resolves with the recorded audio Blob once recording stops.
  const stop = useCallback(() => new Promise((resolve) => {
    const recorder = recorderRef.current
    if (!recorder || recorder.state !== 'recording') return resolve(null)
    resolveRef.current = resolve
    recorder.stop()
  }), [])

  useEffect(() => () => {
    clearTimeout(timerRef.current)
    if (recorderRef.current?.state === 'recording') recorderRef.current.stop()
  }, [])

  return { supported, recording, error, start, stop }
}
