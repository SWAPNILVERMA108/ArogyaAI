from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import HealthCategory, HealthTip

User = get_user_model()


class HealthContentAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_health_tips", verbosity=0)
        cls.user = User.objects.create_user(email="u@example.com", password="StrongPass123!", name="U")

    def test_seed_is_idempotent_and_covers_required_categories(self):
        tip_count = HealthTip.objects.count()
        call_command("seed_health_tips", verbosity=0)
        self.assertEqual(HealthTip.objects.count(), tip_count)
        slugs = set(HealthCategory.objects.values_list("slug", flat=True))
        self.assertEqual(
            slugs,
            {"nutrition", "exercise", "sleep", "hydration", "preventive-care", "general-wellness"},
        )
        self.assertFalse(HealthTip.objects.filter(title_hi="").exists())

    def test_requires_authentication(self):
        self.assertEqual(self.client.get(reverse("health:tips")).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_categories_and_tips_filter_with_disclaimer(self):
        self.client.force_authenticate(self.user)
        categories = self.client.get(reverse("health:categories"))
        self.assertEqual(categories.status_code, status.HTTP_200_OK)
        self.assertEqual(len(categories.data["data"]), 6)
        self.assertTrue(all(item["tip_count"] > 0 for item in categories.data["data"]))

        tips = self.client.get(reverse("health:tips"), {"category": "sleep"})
        self.assertEqual(tips.status_code, status.HTTP_200_OK)
        self.assertTrue(tips.data["data"]["disclaimer"])
        self.assertTrue(all(tip["category"] == "sleep" for tip in tips.data["data"]["tips"]))

    def test_unpublished_tips_are_hidden(self):
        HealthTip.objects.filter(category__slug="sleep").update(is_published=False)
        self.client.force_authenticate(self.user)
        tips = self.client.get(reverse("health:tips"), {"category": "sleep"})
        self.assertEqual(tips.data["data"]["tips"], [])
