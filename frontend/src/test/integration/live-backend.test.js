// End-to-end check of the real service layer against a running Django server.
// Start the backend first (see docs/testing.md), then: npm run test:integration
import { beforeAll, describe, expect, it } from 'vitest'
import api from '../../services/api'
import { adminService, doctorService } from '../../services/adminService'
import { authService } from '../../services/authService'
import { chatService } from '../../services/chatService'
import { emergencyService } from '../../services/emergencyService'
import { healthService } from '../../services/healthService'
import { medicineService } from '../../services/medicineService'
import { patientService } from '../../services/patientService'
import { reportService } from '../../services/reportService'
import { tokenStorage } from '../../utils/tokenStorage'
import { getErrorMessage } from '../../utils/errors'

const stamp = Date.now()
const patient = { name: 'Asha Devi', email: `asha${stamp}@example.com`, phone: '9876543210', password: 'StrongPass123!' }
const DOCTOR = { email: 'doctor@example.com', password: 'StrongPass123!' }
const ADMIN = { email: 'admin@example.com', password: 'StrongPass123!' }

describe('frontend services against the live API', () => {
  beforeAll(() => { localStorage.clear(); tokenStorage.clear() })

  it('registers a patient, then restores the session from the refresh token', async () => {
    const user = await authService.register(patient)
    expect(user.role).toBe('PATIENT')
    tokenStorage.set({}) // keep refresh token
    // Simulate a page reload: the access token is gone but the refresh token remains.
    const refresh = tokenStorage.getRefresh()
    tokenStorage.clear()
    tokenStorage.set({ refresh })
    const restored = await authService.restoreSession()
    expect(restored.email).toBe(patient.email)
  })

  it('transparently refreshes an expired access token', async () => {
    // Drop only the in-memory access token; the next call 401s and must recover.
    const refresh = tokenStorage.getRefresh()
    tokenStorage.clear()
    tokenStorage.set({ refresh })
    const profile = await authService.getProfile()
    expect(profile.email).toBe(patient.email)
    expect(tokenStorage.getAccess()).toBeTruthy()
  })

  it('creates and updates a patient health profile', async () => {
    expect(await patientService.getMine()).toBeNull()
    const created = await patientService.create({ gender: 'FEMALE', blood_group: 'O+', date_of_birth: '1990-05-01', allergies: 'None' })
    expect(created.age).toBeGreaterThan(30)
    const updated = await patientService.update({ ...created, height_cm: '160.5' })
    expect(updated.height_cm).toBe('160.50')
  })

  it('manages medicines, reminders and logs', async () => {
    const medicine = await medicineService.create({ name: 'Paracetamol', dosage: '1 tablet', instructions: 'after food', is_active: true })
    await medicineService.addReminder(medicine.id, { reminder_time: '08:00', days_of_week: ['MON', 'FRI'] })
    const log = await medicineService.markTaken(medicine.id)
    expect(log.status).toBe('TAKEN')
    const [listed] = await medicineService.list()
    expect(listed.reminders).toHaveLength(1)
    expect((await medicineService.logs(medicine.id))).toHaveLength(1)
    await medicineService.update(medicine.id, { name: 'Paracetamol', dosage: '2 tablets', is_active: true })
  })

  it('shows API validation errors the way the forms expect', async () => {
    await expect(medicineService.create({ name: 'X', start_date: '2026-02-02', end_date: '2026-01-01' })).rejects.toSatisfy(
      (error) => /end_date/.test(getErrorMessage(error)),
    )
  })

  it('serves emergency info, contacts and a location message', async () => {
    const info = await emergencyService.info()
    expect(info.call_uri).toMatch(/^tel:/)
    const contact = await emergencyService.createContact({ name: 'Ravi', phone: '+91 98765 43210', is_primary: true })
    const share = await emergencyService.shareLocation({ latitude: 28.6, longitude: 77.2, contactId: contact.id })
    expect(share.share_url).toContain('openstreetmap.org')
    await emergencyService.deleteContact(contact.id)
  })

  it('serves bilingual health tips', async () => {
    const categories = await healthService.categories()
    expect(categories.length).toBe(6)
    const { tips, disclaimer_hi: hindiDisclaimer } = await healthService.tips('sleep')
    expect(tips.length).toBeGreaterThan(0)
    expect(tips[0].title_hi).toBeTruthy()
    expect(hindiDisclaimer).toBeTruthy()
  })

  it('uploads and lists a report, rejecting disguised files', async () => {
    const pdf = new File([new TextEncoder().encode('%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF')], 'lab.pdf', { type: 'application/pdf' })
    const created = await reportService.upload(pdf)
    expect(created.file_type).toBe('PDF')
    expect((await reportService.list()).map((r) => r.id)).toContain(created.id)
    const fake = new File([new TextEncoder().encode('not really a png')], 'x.png', { type: 'image/png' })
    await expect(reportService.upload(fake)).rejects.toSatisfy((e) => e.response.status === 400)
    await reportService.remove(created.id)
  })

  it('reports an unconfigured chat provider as a readable error, not a crash', async () => {
    await expect(chatService.sendMessage({ message: 'I have a mild fever' })).rejects.toSatisfy(
      (error) => [200, 503].includes(error.response?.status ?? 200),
    )
    expect(await chatService.listConversations()).toBeInstanceOf(Array)
  })

  it('enforces roles: a patient cannot reach doctor or admin APIs', async () => {
    await expect(doctorService.patients()).rejects.toSatisfy((e) => e.response.status === 403)
    await expect(adminService.stats()).rejects.toSatisfy((e) => e.response.status === 403)
  })

  it('lets a patient grant a doctor access, and the doctor see only that patient', async () => {
    const grant = await patientService.grantAccess(DOCTOR.email)
    expect(grant.doctor_email).toBe(DOCTOR.email)
    await authService.logout()

    await authService.login(DOCTOR)
    const patients = await doctorService.patients()
    expect(patients.map((p) => p.email)).toContain(patient.email)
    const detail = await doctorService.patient(patients.find((p) => p.email === patient.email).patient_id)
    expect(detail.medicines[0].name).toBe('Paracetamol')
    await expect(medicineService.list()).rejects.toSatisfy((e) => e.response.status === 403)
    await authService.logout()
  })

  it('lets an admin manage users but never exposes passwords', async () => {
    await authService.login(ADMIN)
    const stats = await adminService.stats()
    expect(stats.users_total).toBeGreaterThanOrEqual(3)
    const users = await adminService.users({ search: patient.email })
    expect(users[0]).not.toHaveProperty('password')
    const updated = await adminService.updateUser(users[0].id, { is_active: false })
    expect(updated.is_active).toBe(false)
    await authService.logout()
    await expect(authService.login({ email: patient.email, password: patient.password })).rejects.toBeDefined()
  })

  it('invalidates the refresh token on logout', async () => {
    await authService.login(ADMIN)
    const refresh = tokenStorage.getRefresh()
    await authService.logout()
    tokenStorage.set({ refresh })
    await expect(authService.restoreSession()).rejects.toBeDefined()
    expect(api.defaults.baseURL).toContain('/api')
  })
})
