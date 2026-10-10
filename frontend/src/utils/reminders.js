const DAY_CODES = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']

// Reminders that fall on today's weekday (an empty day list means every day).
export function todaysReminders(medicines) {
  const today = DAY_CODES[new Date().getDay()]
  return medicines
    .filter((medicine) => medicine.is_active)
    .flatMap((medicine) => (medicine.reminders || [])
      .filter((reminder) => reminder.is_active && (!reminder.days_of_week?.length || reminder.days_of_week.includes(today)))
      .map((reminder) => ({ id: reminder.id, name: medicine.name, dosage: medicine.dosage, time: reminder.reminder_time })))
    .sort((a, b) => a.time.localeCompare(b.time))
}

