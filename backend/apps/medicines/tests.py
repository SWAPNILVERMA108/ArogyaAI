from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import MedicationLog, Medicine, MedicineReminder


User = get_user_model()


class MedicineAPITests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            email="medicine-patient@example.com", name="Mina Patient", password="StrongPass123!"
        )
        self.other_patient = User.objects.create_user(
            email="medicine-other@example.com", name="Other Patient", password="StrongPass123!"
        )
        self.client.force_authenticate(self.patient)

    def create_medicine(self, name="Vitamin D"):
        return self.client.post(
            reverse("medicines:list-create"),
            {"name": name, "dosage": "1 tablet", "instructions": "As directed by my clinician"},
            format="json",
        )

    def test_patient_can_create_list_update_and_delete_medicine(self):
        create = self.create_medicine()
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        medicine_id = create.data["data"]["id"]
        self.assertEqual(create.data["data"]["user"], self.patient.id)

        listed = self.client.get(reverse("medicines:list-create"))
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listed.data["data"]), 1)

        updated = self.client.put(
            reverse("medicines:detail", args=[medicine_id]),
            {"name": "Vitamin D3", "dosage": "2 tablets"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["data"]["name"], "Vitamin D3")

        deleted = self.client.delete(reverse("medicines:detail", args=[medicine_id]))
        self.assertEqual(deleted.status_code, status.HTTP_200_OK)
        self.assertFalse(Medicine.objects.filter(pk=medicine_id).exists())

    def test_medicine_cannot_be_read_or_changed_by_another_patient(self):
        medicine = Medicine.objects.create(user=self.other_patient, name="Private medicine")
        response = self.client.get(reverse("medicines:detail", args=[medicine.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.put(
            reverse("medicines:detail", args=[medicine.id]), {"name": "Changed"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patient_can_manage_reminder_schedule(self):
        medicine = self.create_medicine().data["data"]
        medicine_id = medicine["id"]

        created = self.client.post(
            reverse("medicines:reminders", args=[medicine_id]),
            {"reminder_time": "08:30:00", "days_of_week": ["MON", "WED", "FRI"]},
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        reminder_id = created.data["data"]["id"]
        self.assertEqual(created.data["data"]["days_of_week"], ["MON", "WED", "FRI"])

        listed = self.client.get(reverse("medicines:reminders", args=[medicine_id]))
        self.assertEqual(len(listed.data["data"]), 1)

        updated = self.client.patch(
            reverse("medicines:reminder-detail", args=[medicine_id, reminder_id]),
            {"is_active": False},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertFalse(updated.data["data"]["is_active"])

        deleted = self.client.delete(reverse("medicines:reminder-detail", args=[medicine_id, reminder_id]))
        self.assertEqual(deleted.status_code, status.HTTP_200_OK)
        self.assertFalse(MedicineReminder.objects.filter(pk=reminder_id).exists())

    def test_duplicate_reminder_time_returns_conflict(self):
        medicine = self.create_medicine().data["data"]
        url = reverse("medicines:reminders", args=[medicine["id"]])
        payload = {"reminder_time": "08:30:00", "days_of_week": ["MON"]}
        self.assertEqual(self.client.post(url, payload, format="json").status_code, status.HTTP_201_CREATED)
        duplicate = self.client.post(url, payload, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_409_CONFLICT)

    def test_mark_taken_records_log_and_lists_history(self):
        medicine = self.create_medicine().data["data"]
        medicine_id = medicine["id"]
        marked = self.client.post(
            reverse("medicines:taken", args=[medicine_id]), {"note": "Taken after breakfast"}, format="json"
        )
        self.assertEqual(marked.status_code, status.HTTP_201_CREATED)
        self.assertEqual(marked.data["data"]["status"], MedicationLog.Status.TAKEN)
        self.assertEqual(marked.data["data"]["note"], "Taken after breakfast")
        history = self.client.get(reverse("medicines:logs", args=[medicine_id]))
        self.assertEqual(len(history.data["data"]), 1)

    def test_inactive_medicine_cannot_be_marked_taken(self):
        medicine = Medicine.objects.create(user=self.patient, name="Stopped", is_active=False)
        response = self.client.post(reverse("medicines:taken", args=[medicine.id]), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_invalid_date_range_and_duplicate_weekday_are_rejected(self):
        invalid_medicine = self.client.post(
            reverse("medicines:list-create"),
            {"name": "Invalid", "start_date": "2026-04-01", "end_date": "2026-03-01"},
            format="json",
        )
        self.assertEqual(invalid_medicine.status_code, status.HTTP_400_BAD_REQUEST)

        medicine = self.create_medicine().data["data"]
        invalid_reminder = self.client.post(
            reverse("medicines:reminders", args=[medicine["id"]]),
            {"reminder_time": "08:30:00", "days_of_week": ["MON", "MON"]},
            format="json",
        )
        self.assertEqual(invalid_reminder.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_patient_and_anonymous_users_are_denied(self):
        doctor = User.objects.create_user(
            email="doctor@example.com", name="Doctor", password="StrongPass123!", role=User.Role.DOCTOR
        )
        self.client.force_authenticate(doctor)
        response = self.client.get(reverse("medicines:list-create"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("medicines:list-create"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MedicineRemindersInListTests(APITestCase):
    def test_medicine_payload_includes_its_reminders(self):
        user = User.objects.create_user(email="rem@example.com", password="StrongPass123!", name="Rem")
        medicine = Medicine.objects.create(user=user, name="Iron")
        MedicineReminder.objects.create(medicine=medicine, reminder_time="08:00", days_of_week=["MON"])
        self.client.force_authenticate(user)
        response = self.client.get("/api/medicines/")
        reminders = response.data["data"][0]["reminders"]
        self.assertEqual(len(reminders), 1)
        self.assertEqual(reminders[0]["days_of_week"], ["MON"])
