import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ProtectedRoute from '../components/ProtectedRoute'
import { LanguageProvider } from '../context/LanguageContext'
import LoginPage from '../pages/LoginPage'

const authState = { user: null, initialising: false, login: vi.fn() }
vi.mock('../context/AuthContext', () => ({ useAuth: () => authState }))

const renderAt = (path, ui) => render(
  <LanguageProvider><MemoryRouter initialEntries={[path]}>{ui}</MemoryRouter></LanguageProvider>,
)

const guarded = (roles) => (
  <Routes>
    <Route path="/login" element={<p>login screen</p>} />
    <Route path="/dashboard" element={<p>patient home</p>} />
    <Route path="/doctor/dashboard" element={<p>doctor home</p>} />
    <Route element={<ProtectedRoute roles={roles} />}><Route path="/secret" element={<p>secret page</p>} /></Route>
  </Routes>
)

describe('ProtectedRoute', () => {
  beforeEach(() => { authState.user = null; authState.initialising = false })

  it('redirects anonymous visitors to login', () => {
    renderAt('/secret', guarded())
    expect(screen.getByText('login screen')).toBeInTheDocument()
  })
  it('renders for a signed-in user with an allowed role', () => {
    authState.user = { role: 'PATIENT', name: 'A' }
    renderAt('/secret', guarded(['PATIENT']))
    expect(screen.getByText('secret page')).toBeInTheDocument()
  })
  it("sends users with the wrong role to their own home", () => {
    authState.user = { role: 'DOCTOR', name: 'D' }
    renderAt('/secret', guarded(['PATIENT']))
    expect(screen.getByText('doctor home')).toBeInTheDocument()
  })
})

describe('LoginPage', () => {
  beforeEach(() => { authState.user = null; authState.login = vi.fn() })

  it('validates required fields before calling the API', async () => {
    renderAt('/login', <LoginPage />)
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))
    expect(await screen.findByText('Email is required.')).toBeInTheDocument()
    expect(authState.login).not.toHaveBeenCalled()
  })
  it('shows the server error for bad credentials', async () => {
    authState.login = vi.fn().mockRejectedValue({ response: { data: { error: { message: 'Invalid email or password.', details: { non_field_errors: ['Invalid email or password.'] } } } } })
    renderAt('/login', <LoginPage />)
    await userEvent.type(screen.getByLabelText(/email/i), 'a@b.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'wrong-pass')
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password.')
  })
})
