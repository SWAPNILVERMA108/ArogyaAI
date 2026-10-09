from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import PatientProfile


User = get_user_model()


class PatientProfileAPITests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            email="patient@example.com", name="Patient One", password="StrongPass123!"
        )
        self.other_patient = User.objects.create_user(
            email="other@example.com", name="Patient Two", password="StrongPass123!"
        )
        self.client.force_authenticate(self.patient)

    def test_patient_can_create_read_and_update_own_profile(self):
        create = self.client.post(
            reverse("patients:create"),
            {
                "date_of_birth": "1995-06-12",
                "gender": "FEMALE",
                "blood_group": "O+",
                "height_cm": "160.00",
                "weight_kg": "55.00",
                "allergies": "Pollen",
                "medical_history": "None reported",
                "emergency_contact": "+91 98765 43210",
            },
            format="json",
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        profile_id = create.data["data"]["id"]
        self.assertEqual(create.data["data"]["user"], self.patient.id)
        self.assertEqual(create.data["data"]["age"], date.today().year - 1995 - ((date.today().month, date.today().day) < (6, 12)))

        mine = self.client.get(reverse("patients:me"))
        self.assertEqual(mine.status_code, status.HTTP_200_OK)

        update = self.client.put(
            reverse("patients:me"), {"allergies": "Pollen, dust"}, format="json"
        )
        self.assertEqual(update.status_code, status.HTTP_200_OK)
        self.assertEqual(update.data["data"]["allergies"], "Pollen, dust")

        detail = self.client.get(reverse("patients:detail", args=[profile_id]))
        self.assertEqual(detail.status_code, status.HTTP_200_OK)

    def test_profile_creation_cannot_assign_another_user(self):
        response = self.client.post(
            reverse("patients:create"), {"user": self.other_patient.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["user"], self.patient.id)

    def test_duplicate_profile_returns_conflict(self):
        PatientProfile.objects.create(user=self.patient)
        response = self.client.post(reverse("patients:create"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["error"]["code"], "conflict")

    def test_patient_cannot_access_another_patients_profile(self):
        other_profile = PatientProfile.objects.create(user=self.other_patient)
        response = self.client.get(reverse("patients:detail", args=[other_profile.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patient_endpoints_require_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("patients:me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_future_date_of_birth_is_invalid(self):
        response = self.client.post(
            reverse("patients:create"),
            {"date_of_birth": "2999-01-01"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
