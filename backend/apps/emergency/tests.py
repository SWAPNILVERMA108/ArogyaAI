import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import EmergencyContact


User = get_user_model()


class EmergencyAPITests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            email="emergency-patient@example.com", name="Emergency Patient", password="StrongPass123!"
        )
        self.other_patient = User.objects.create_user(
            email="emergency-other@example.com", name="Other Patient", password="StrongPass123!"
        )
        self.client.force_authenticate(self.patient)

    def test_emergency_info_returns_india_call_link_and_clear_disclaimer(self):
        with patch.dict(os.environ, {"EMERGENCY_SERVICES_NUMBER": "112"}):
            response = self.client.get(reverse("emergency:info"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(data["emergency_number"], "112")
        self.assertEqual(data["call_uri"], "tel:112")
        self.assertIn("cannot dispatch help", data["disclaimer"])
        self.assertTrue(data["guidance"])

    def test_patient_can_create_list_update_and_delete_own_contacts(self):
        created = self.client.post(
            reverse("emergency:contacts"),
            {"name": "Family contact", "phone": "+91 98765 43210", "relationship": "Sibling", "is_primary": True},
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        contact_id = created.data["data"]["id"]

        listed = self.client.get(reverse("emergency:contacts"))
        self.assertEqual(len(listed.data["data"]), 1)

        updated = self.client.patch(
            reverse("emergency:contact-detail", args=[contact_id]),
            {"phone": "+91 98765 43211"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["data"]["phone"], "+91 98765 43211")

        deleted = self.client.delete(reverse("emergency:contact-detail", args=[contact_id]))
        self.assertEqual(deleted.status_code, status.HTTP_200_OK)
        self.assertFalse(EmergencyContact.objects.filter(pk=contact_id).exists())

    def test_primary_contact_is_unique_per_user(self):
        EmergencyContact.objects.create(
            user=self.patient, name="First", phone="1234567890", is_primary=True
        )
        response = self.client.post(
            reverse("emergency:contacts"),
            {"name": "Second", "phone": "1234567891", "is_primary": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_contacts_are_private_to_their_owner(self):
        contact = EmergencyContact.objects.create(
            user=self.other_patient, name="Private", phone="1234567890"
        )
        response = self.client.get(reverse("emergency:contact-detail", args=[contact.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_location_share_prepares_message_without_sending_or_saving_location(self):
        contact = EmergencyContact.objects.create(
            user=self.patient, name="Trusted contact", phone="1234567890"
        )
        response = self.client.post(
            reverse("emergency:location-share"),
            {"latitude": 12.9716, "longitude": 77.5946, "emergency_contact_id": contact.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertIn("mlat=12.9716", data["share_url"])
        self.assertEqual(data["contact"]["id"], contact.pk)
        self.assertIn("no message is sent automatically", data["notice"])
        self.assertEqual(EmergencyContact.objects.count(), 1)

    def test_location_share_cannot_use_another_users_contact(self):
        contact = EmergencyContact.objects.create(
            user=self.other_patient, name="Not yours", phone="1234567890"
        )
        response = self.client.post(
            reverse("emergency:location-share"),
            {"latitude": 12.9, "longitude": 77.5, "emergency_contact_id": contact.pk},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_coordinates_and_contact_phone_are_rejected(self):
        invalid_location = self.client.post(
            reverse("emergency:location-share"),
            {"latitude": 91, "longitude": 77.5},
            format="json",
        )
        invalid_phone = self.client.post(
            reverse("emergency:contacts"),
            {"name": "Contact", "phone": "123"},
            format="json",
        )
        self.assertEqual(invalid_location.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(invalid_phone.status_code, status.HTTP_400_BAD_REQUEST)

    def test_anonymous_users_cannot_access_emergency_endpoints(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("emergency:info"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
