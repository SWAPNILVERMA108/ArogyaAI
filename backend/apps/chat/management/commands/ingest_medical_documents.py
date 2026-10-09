from django.core.management.base import BaseCommand, CommandError

from ai.rag.pipeline import RAGPipeline


class Command(BaseCommand):
    help = "Build the local FAISS index from reviewed PDF, Markdown, and text references."

    def handle(self, *args, **options):
        try:
            result = RAGPipeline().ingest()
        except (OSError, ValueError, RuntimeError) as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Indexed {result['chunks']} chunks from "
                f"{result['source_documents']} source document(s)."
            )
        )
