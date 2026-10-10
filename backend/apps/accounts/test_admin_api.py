from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AdminAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            email="a@example.com", password="StrongPass123!", name="Admin", role=User.Role.ADMIN
        )
        cls.patient = User.objects.create_user(email="p@example.com", password="StrongPass123!", name="Pat")

    def test_non_admin_is_forbidden(self):
        self.client.force_authenticate(self.patient)
        for name in ("admin_api:users", "admin_api:stats"):
            self.assertEqual(self.client.get(reverse(name)).status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_lists_filters_and_never_sees_passwords(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse("admin_api:users"), {"role": "PATIENT", "search": "pat"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([u["email"] for u in response.data["data"]], ["p@example.com"])
        self.assertNotIn("password", response.data["data"][0])

    def test_admin_promotes_user_and_cannot_edit_self(self):
        self.client.force_authenticate(self.admin)
        url = reverse("admin_api:user-detail", args=[self.patient.id])
        response = self.client.patch(url, {"role": "DOCTOR"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.role, User.Role.DOCTOR)

        own = self.client.patch(reverse("admin_api:user-detail", args=[self.admin.id]), {"is_active": False}, format="json")
        self.assertEqual(own.status_code, status.HTTP_403_FORBIDDEN)
        bad = self.client.patch(url, {"role": "SUPERUSER"}, format="json")
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stats_are_aggregate_only(self):
        self.client.force_authenticate(self.admin)
        data = self.client.get(reverse("admin_api:stats")).data["data"]
        self.assertEqual(data["users_total"], 2)
        self.assertEqual(data["users_by_role"]["ADMIN"], 1)
