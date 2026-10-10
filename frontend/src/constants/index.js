export const ROLES = { PATIENT: 'PATIENT', DOCTOR: 'DOCTOR', ADMIN: 'ADMIN' }

export const HOME_BY_ROLE = {
  PATIENT: '/dashboard',
  DOCTOR: '/doctor/dashboard',
  ADMIN: '/admin/dashboard',
}

export const WEEKDAYS = [
  { value: 'MON', en: 'Mon', hi: 'सोम' },
  { value: 'TUE', en: 'Tue', hi: 'मंगल' },
  { value: 'WED', en: 'Wed', hi: 'बुध' },
  { value: 'THU', en: 'Thu', hi: 'गुरु' },
  { value: 'FRI', en: 'Fri', hi: 'शुक्र' },
  { value: 'SAT', en: 'Sat', hi: 'शनि' },
  { value: 'SUN', en: 'Sun', hi: 'रवि' },
]

export const FACILITY_CATEGORIES = ['hospital', 'clinic', 'pharmacy', 'emergency']
export const GENDERS = ['FEMALE', 'MALE', 'OTHER', 'PREFER_NOT_TO_SAY']
export const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'UNKNOWN']
export const MAX_REPORT_BYTES = 10 * 1024 * 1024
