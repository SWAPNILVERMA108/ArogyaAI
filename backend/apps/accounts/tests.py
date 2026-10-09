from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class AuthenticationAPITests(APITestCase):
    register_url = reverse("accounts:register")
    login_url = reverse("accounts:login")
    profile_url = reverse("accounts:profile")
    refresh_url = reverse("accounts:token-refresh")
    logout_url = reverse("accounts:logout")

    def register(self, **overrides):
        payload = {
            "name": "Asha Devi",
            "email": "asha@example.com",
            "phone": "+91 98765 43210",
            "password": "StrongPass123!",
        }
        payload.update(overrides)
        return self.client.post(self.register_url, payload, format="json")

    def test_registration_creates_patient_and_returns_jwt_tokens(self):
        response = self.register(role="ADMIN")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["user"]["role"], User.Role.PATIENT)
        self.assertIn("access", response.data["data"]["tokens"])
        self.assertIn("refresh", response.data["data"]["tokens"])
        self.assertTrue(User.objects.filter(email="asha@example.com").exists())

    def test_duplicate_email_is_rejected(self):
        self.register()
        response = self.register()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_login_profile_refresh_and_logout_flow(self):
        registration = self.register()
        tokens = registration.data["data"]["tokens"]

        login = self.client.post(
            self.login_url,
            {"email": "asha@example.com", "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)

        access = login.data["data"]["tokens"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        profile = self.client.get(self.profile_url)
        self.assertEqual(profile.status_code, status.HTTP_200_OK)
        self.assertEqual(profile.data["data"]["email"], "asha@example.com")

        updated = self.client.put(self.profile_url, {"name": "Asha Kumari"}, format="json")
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["data"]["name"], "Asha Kumari")

        refreshed = self.client.post(self.refresh_url, {"refresh": tokens["refresh"]}, format="json")
        self.assertEqual(refreshed.status_code, status.HTTP_200_OK)
        self.assertIn("access", refreshed.data["data"])

        logout = self.client.post(self.logout_url, {"refresh": login.data["data"]["tokens"]["refresh"]}, format="json")
        self.assertEqual(logout.status_code, status.HTTP_205_RESET_CONTENT)

    def test_profile_requires_authentication(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
