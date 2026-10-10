import { describe, expect, it, vi } from 'vitest'
import { getErrorMessage, getFieldErrors } from '../utils/errors'
import { todaysReminders } from '../utils/reminders'
import { formatBytes, formatTime } from '../utils/format'

describe('error helpers', () => {
  it('prefers field errors from the API envelope', () => {
    const error = { response: { data: { error: { message: 'x', details: { email: ['Already exists.'] } } } } }
    expect(getErrorMessage(error)).toBe('email: Already exists.')
    expect(getFieldErrors(error)).toEqual({ email: 'Already exists.' })
  })
  it('explains network failures', () => {
    expect(getErrorMessage({ code: 'ERR_NETWORK' })).toMatch(/internet connection/i)
  })
  it('falls back to the API message', () => {
    expect(getErrorMessage({ response: { data: { error: { message: 'Nope', details: { detail: 'Nope' } } } } })).toBe('Nope')
  })
})

describe('todaysReminders', () => {
  const medicines = [
    { name: 'A', dosage: '1', is_active: true, reminders: [
      { id: 1, reminder_time: '20:00:00', days_of_week: [], is_active: true },
      { id: 2, reminder_time: '08:00:00', days_of_week: ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'], is_active: true },
      { id: 3, reminder_time: '09:00:00', days_of_week: [], is_active: false },
    ] },
    { name: 'Stopped', is_active: false, reminders: [{ id: 4, reminder_time: '07:00:00', days_of_week: [], is_active: true }] },
  ]
  it('keeps active reminders for today, sorted by time', () => {
    vi.setSystemTime(new Date('2026-10-10T10:00:00')) // a Saturday
    expect(todaysReminders(medicines).map((r) => r.id)).toEqual([2, 1])
  })
  it('skips reminders for other weekdays', () => {
    vi.setSystemTime(new Date('2026-10-10T10:00:00'))
    const only = [{ name: 'B', is_active: true, reminders: [{ id: 9, reminder_time: '06:00:00', days_of_week: ['MON'], is_active: true }] }]
    expect(todaysReminders(only)).toEqual([])
  })
})

describe('formatters', () => {
  it('formats time and size', () => {
    expect(formatTime('08:30:00')).toBe('08:30')
    expect(formatBytes(2 * 1024 * 1024)).toBe('2.0 MB')
  })
})
