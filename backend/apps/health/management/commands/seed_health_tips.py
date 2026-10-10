from django.core.management.base import BaseCommand

from apps.health.services import DEFAULT_CONTENT_PATH, HealthContentService


class Command(BaseCommand):
    help = "Load curated general wellness tips from backend/data/health_tips.json (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--path", default=str(DEFAULT_CONTENT_PATH))

    def handle(self, *args, **options):
        created = HealthContentService.load_from_file(options["path"])
        self.stdout.write(self.style.SUCCESS(f"Health tips loaded ({created} new)."))
