from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.medicines.models import Medicine

from .models import PatientProfile

User = get_user_model()


class DoctorAccessTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.patient = User.objects.create_user(email="p@example.com", password="StrongPass123!", name="Patient")
        cls.other = User.objects.create_user(email="o@example.com", password="StrongPass123!", name="Other")
        cls.doctor = User.objects.create_user(
            email="d@example.com", password="StrongPass123!", name="Doc", role=User.Role.DOCTOR
        )
        PatientProfile.objects.create(user=cls.patient, blood_group="O+")
        Medicine.objects.create(user=cls.patient, name="Paracetamol", dosage="500 mg")
        Medicine.objects.create(user=cls.patient, name="Old", is_active=False)

    def test_doctor_sees_nothing_without_patient_consent(self):
        self.client.force_authenticate(self.doctor)
        response = self.client.get(reverse("doctor:patients"))
        self.assertEqual(response.data["data"], [])
        detail = self.client.get(reverse("doctor:patient-detail", args=[self.patient.id]))
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_patient_grants_and_revokes_access(self):
        self.client.force_authenticate(self.patient)
        grant = self.client.post(reverse("patients:access"), {"doctor_email": "D@example.com"}, format="json")
        self.assertEqual(grant.status_code, status.HTTP_201_CREATED)
        duplicate = self.client.post(reverse("patients:access"), {"doctor_email": "d@example.com"}, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_409_CONFLICT)

        self.client.force_authenticate(self.doctor)
        listing = self.client.get(reverse("doctor:patients"))
        self.assertEqual([p["patient_id"] for p in listing.data["data"]], [self.patient.id])
        detail = self.client.get(reverse("doctor:patient-detail", args=[self.patient.id]))
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual([m["name"] for m in detail.data["data"]["medicines"]], ["Paracetamol"])

        self.client.force_authenticate(self.patient)
        revoke = self.client.delete(reverse("patients:access-detail", args=[grant.data["data"]["id"]]))
        self.assertEqual(revoke.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(self.doctor)
        self.assertEqual(self.client.get(reverse("doctor:patients")).data["data"], [])

    def test_grant_requires_existing_doctor(self):
        self.client.force_authenticate(self.patient)
        response = self.client.post(reverse("patients:access"), {"doctor_email": "o@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patient_cannot_use_doctor_endpoints_or_revoke_others_grants(self):
        self.client.force_authenticate(self.patient)
        self.assertEqual(self.client.get(reverse("doctor:patients")).status_code, status.HTTP_403_FORBIDDEN)
        self.client.post(reverse("patients:access"), {"doctor_email": "d@example.com"}, format="json")
        grant_id = self.patient.access_grants.first().id
        self.client.force_authenticate(self.other)
        self.assertEqual(
            self.client.delete(reverse("patients:access-detail", args=[grant_id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )
