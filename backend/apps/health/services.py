import json
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q

from .models import HealthCategory, HealthTip

TIPS_DISCLAIMER = (
    "These are general wellness tips for the public. They are not personalized "
    "medical advice, diagnosis, or treatment. Speak to a qualified health "
    "professional about your own situation."
)
TIPS_DISCLAIMER_HI = (
    "ये सामान्य स्वास्थ्य सुझाव हैं, व्यक्तिगत चिकित्सा सलाह, निदान या इलाज नहीं। "
    "अपनी स्थिति के लिए किसी योग्य स्वास्थ्य विशेषज्ञ से सलाह लें।"
)
DEFAULT_CONTENT_PATH = Path(settings.BASE_DIR) / "data" / "health_tips.json"


class HealthContentService:
    @staticmethod
    def categories():
        return HealthCategory.objects.annotate(
            tip_count=Count("tips", filter=Q(tips__is_published=True))
        )

    @staticmethod
    def tips(category_slug=None):
        tips = HealthTip.objects.filter(is_published=True).select_related("category")
        if category_slug:
            tips = tips.filter(category__slug=category_slug)
        return tips

    @staticmethod
    @transaction.atomic
    def load_from_file(path=DEFAULT_CONTENT_PATH):
        """Idempotently load curated categories and tips from a JSON file."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        created_tips = 0
        for category_order, item in enumerate(payload["categories"]):
            category, _ = HealthCategory.objects.update_or_create(
                slug=item["slug"],
                defaults={"name": item["name"], "name_hi": item.get("name_hi", ""), "order": category_order},
            )
            for tip_order, tip in enumerate(item["tips"]):
                _, created = HealthTip.objects.update_or_create(
                    slug=tip["slug"],
                    defaults={
                        "category": category,
                        "title": tip["title"],
                        "title_hi": tip.get("title_hi", ""),
                        "body": tip["body"],
                        "body_hi": tip.get("body_hi", ""),
                        "order": tip_order,
                        "is_published": True,
                    },
                )
                created_tips += int(created)
        return created_tips
