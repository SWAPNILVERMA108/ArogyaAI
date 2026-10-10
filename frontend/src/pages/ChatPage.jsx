import { Eraser, Menu, Mic, Plus, Send, Square, Trash2, Volume2, X } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import Disclaimer from '../components/Disclaimer'
import { Alert, Button, Spinner, inputClass } from '../components/ui'
import { useLanguage } from '../context/LanguageContext'
import { useVoiceRecorder } from '../hooks/useVoiceRecorder'
import { chatService } from '../services/chatService'
import { voiceService } from '../services/voiceService'
import { getErrorMessage } from '../utils/errors'
import { formatDateTime } from '../utils/format'

function MessageBubble({ message, onListen, listening }) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[88%] rounded-2xl px-4 py-3 text-base ${isUser ? 'bg-brand-700 text-white' : 'border border-slate-200 bg-white'}`}>
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
        {!isUser && message.sources?.length > 0 && (
          <p className="mt-2 border-t border-slate-100 pt-2 text-sm text-slate-600">
            Sources: {message.sources.map((s) => `${s.source}${s.page ? ` (p. ${s.page})` : ''}`).join(', ')}
          </p>
        )}
        {!isUser && message.id !== 'pending' && (
          <button onClick={() => onListen(message)} disabled={listening} className="mt-2 flex min-h-10 items-center gap-1 text-sm font-semibold text-brand-700 disabled:opacity-50">
            <Volume2 className="size-4" aria-hidden /> Listen
          </button>
        )}
      </div>
    </div>
  )
}

export default function ChatPage() {
  const { language } = useLanguage()
  const [params] = useSearchParams()
  const [conversations, setConversations] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [voiceMode, setVoiceMode] = useState(params.get('voice') === '1')
  const [consent, setConsent] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [disclaimer, setDisclaimer] = useState('')
  const bottomRef = useRef(null)
  const audioRef = useRef(null)
  const recorder = useVoiceRecorder()

  const refreshConversations = useCallback(async () => {
    try { setConversations(await chatService.listConversations()) } catch (err) { setError(getErrorMessage(err)) }
  }, [])

  useEffect(() => { refreshConversations() }, [refreshConversations])
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, sending])
  useEffect(() => () => audioRef.current?.pause(), [])

  const openConversation = async (id) => {
    setError('')
    setDrawerOpen(false)
    try {
      const detail = await chatService.getConversation(id)
      setActiveId(id)
      setMessages(detail.messages)
    } catch (err) { setError(getErrorMessage(err)) }
  }

  const startNew = () => { setActiveId(null); setMessages([]); setError(''); setDrawerOpen(false) }

  const listen = async (message) => {
    setSpeaking(true)
    setError('')
    try {
      const blob = await voiceService.speak(message.content.slice(0, 3000), language)
      audioRef.current?.pause()
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audio.onended = () => URL.revokeObjectURL(url)
      audioRef.current = audio
      await audio.play()
    } catch (err) { setError(getErrorMessage(err)) } finally { setSpeaking(false) }
  }

  const send = async (event) => {
    event?.preventDefault()
    const text = input.trim()
    if (!text || sending) return
    setError('')
    setInput('')
    setSending(true)
    setMessages((current) => [...current, { id: `local-${Date.now()}`, role: 'user', content: text }])
    try {
      const result = await chatService.sendMessage({ message: text, conversationId: activeId })
      const reply = { id: `reply-${Date.now()}`, role: 'assistant', content: result.message, sources: result.sources }
      setMessages((current) => [...current, reply])
      setDisclaimer(result.disclaimer)
      if (!activeId) setActiveId(result.conversation_id)
      refreshConversations()
      if (voiceMode && consent) listen(reply)
    } catch (err) {
      setError(getErrorMessage(err))
      setInput(text) // let the person retry without retyping
      setMessages((current) => current.slice(0, -1))
    } finally { setSending(false) }
  }

  const toggleMic = async () => {
    setError('')
    if (recorder.recording) {
      const blob = await recorder.stop()
      if (!blob?.size) return
      setTranscribing(true)
      try {
        const { transcript } = await voiceService.transcribe(blob, language)
        setInput((current) => `${current} ${transcript}`.trim()) // review before sending
      } catch (err) { setError(getErrorMessage(err)) } finally { setTranscribing(false) }
    } else {
      if (!consent) { setError('Please tick the consent box first: your voice is sent to Google Gemini to be processed.'); return }
      await recorder.start()
    }
  }

  const clearActive = async () => {
    if (!activeId || !window.confirm('Clear all messages in this conversation?')) return
    try { await chatService.clearMessages(activeId); setMessages([]); refreshConversations() } catch (err) { setError(getErrorMessage(err)) }
  }
  const deleteActive = async () => {
    if (!activeId || !window.confirm('Delete this conversation?')) return
    try { await chatService.deleteConversation(activeId); startNew(); refreshConversations() } catch (err) { setError(getErrorMessage(err)) }
  }

  const sidebar = (
    <div className="flex h-full flex-col gap-3">
      <Button onClick={startNew} className="w-full"><Plus className="size-5" aria-hidden /> New chat</Button>
      <ul className="-mx-1 flex-1 space-y-1 overflow-y-auto px-1">
        {conversations.map((c) => (
          <li key={c.id}>
            <button onClick={() => openConversation(c.id)} className={`w-full rounded-xl px-3 py-2 text-left ${c.id === activeId ? 'bg-brand-100 font-semibold' : 'hover:bg-slate-100'}`}>
              <span className="line-clamp-1">{c.title}</span>
              <span className="block text-xs text-slate-500">{formatDateTime(c.updated_at)}</span>
            </button>
          </li>
        ))}
        {!conversations.length && <li className="p-2 text-sm text-slate-500">No conversations yet.</li>}
      </ul>
    </div>
  )

  return (
    <div className="grid gap-4 lg:grid-cols-[17rem_1fr]">
      <aside className="hidden max-h-[70vh] rounded-2xl border border-slate-200 bg-white p-3 lg:block">{sidebar}</aside>
      {drawerOpen && (
        <div className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={() => setDrawerOpen(false)}>
          <div className="h-full w-72 bg-white p-3" onClick={(e) => e.stopPropagation()}>
            <button className="mb-2 ml-auto block p-2" onClick={() => setDrawerOpen(false)} aria-label="Close"><X /></button>
            {sidebar}
          </div>
        </div>
      )}

      <section className="flex min-h-[70vh] flex-col rounded-2xl border border-slate-200 bg-slate-100">
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 bg-white p-3 lg:rounded-t-2xl">
          <button className="p-2 lg:hidden" onClick={() => setDrawerOpen(true)} aria-label="Conversations"><Menu /></button>
          <h1 className="flex-1 text-xl font-bold">AI Health Assistant</h1>
          <label className="flex min-h-10 items-center gap-2 text-sm font-semibold">
            <input type="checkbox" className="size-5" checked={voiceMode} onChange={(e) => setVoiceMode(e.target.checked)} /> Voice mode
          </label>
          {activeId && (
            <>
              <button onClick={clearActive} className="p-2 text-slate-600" aria-label="Clear messages" title="Clear messages"><Eraser /></button>
              <button onClick={deleteActive} className="p-2 text-red-600" aria-label="Delete conversation" title="Delete conversation"><Trash2 /></button>
            </>
          )}
        </div>

        <div className="flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">
          {!messages.length && (
            <div className="py-10 text-center text-slate-600">
              <p className="text-lg font-semibold text-slate-800">Ask a general health question</p>
              <p>For example: &quot;What can I do for a mild fever?&quot;</p>
              <p className="mt-3 text-sm">Having severe chest pain, trouble breathing, or heavy bleeding? <Link to="/emergency" className="font-bold text-red-700 underline">Go to Emergency</Link></p>
            </div>
          )}
          {messages.map((m) => <MessageBubble key={m.id} message={m} onListen={listen} listening={speaking} />)}
          {sending && <Spinner label="Thinking…" />}
          <div ref={bottomRef} />
        </div>

        <div className="space-y-2 border-t border-slate-200 bg-white p-3 lg:rounded-b-2xl">
          {error && <Alert tone="error">{error}</Alert>}
          {(voiceMode || recorder.recording) && (
            <label className="flex items-start gap-2 text-sm">
              <input type="checkbox" className="mt-0.5 size-5" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
              <span>I agree that my voice recording and text are sent to Google Gemini for speech-to-text and text-to-speech. They are not stored by ArogyaAI.</span>
            </label>
          )}
          {recorder.error && <Alert tone="warning">{recorder.error}</Alert>}
          <form onSubmit={send} className="flex gap-2">
            <label htmlFor="chat-input" className="sr-only">Your question</label>
            <textarea id="chat-input" rows={2} value={input} maxLength={4000} onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) send(e) }}
              placeholder={transcribing ? 'Converting your voice to text…' : 'Type your question here'} className={`${inputClass} resize-none`} />
            {voiceMode && recorder.supported && (
              <Button variant={recorder.recording ? 'danger' : 'secondary'} onClick={toggleMic} loading={transcribing} aria-label={recorder.recording ? 'Stop recording' : 'Start recording'}>
                {recorder.recording ? <Square className="size-5" /> : <Mic className="size-5" />}
              </Button>
            )}
            <Button type="submit" loading={sending} disabled={!input.trim()} aria-label="Send"><Send className="size-5" /></Button>
          </form>
          <Disclaimer text={disclaimer || undefined} />
        </div>
      </section>
    </div>
  )
}
