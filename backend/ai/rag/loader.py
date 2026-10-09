from pathlib import Path

from django.conf import settings
from langchain_core.documents import Document
from pypdf import PdfReader


SUPPORTED_SUFFIXES = {".pdf", ".txt", ".md"}
MAX_DOCUMENT_SIZE_BYTES = 25 * 1024 * 1024


class DocumentLoadError(Exception):
    """Raised when a trusted source document cannot be read safely."""


def load_documents(source_dir=None):
    root = Path(source_dir or settings.BASE_DIR / "data" / "medical").resolve()
    if not root.is_dir():
        raise DocumentLoadError(f"Medical source directory does not exist: {root}")

    documents = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name.startswith(".") or path.name.casefold() == "readme.md":
            continue
        resolved_path = path.resolve()
        try:
            relative_path = resolved_path.relative_to(root)
        except ValueError:
            continue

        suffix = resolved_path.suffix.casefold()
        if suffix not in SUPPORTED_SUFFIXES:
            continue
        if resolved_path.stat().st_size > MAX_DOCUMENT_SIZE_BYTES:
            raise DocumentLoadError(f"Source document exceeds the 25 MB limit: {relative_path}")

        if suffix == ".pdf":
            documents.extend(_load_pdf(resolved_path, relative_path.as_posix()))
        else:
            documents.extend(_load_text(resolved_path, relative_path.as_posix()))
    return [document for document in documents if document.page_content.strip()]


def _load_pdf(path, source):
    try:
        reader = PdfReader(str(path), strict=False)
        if reader.is_encrypted:
            raise DocumentLoadError(f"Encrypted PDF cannot be ingested: {source}")
        return [
            Document(
                page_content=page.extract_text() or "",
                metadata={"source": source, "page": page_number},
            )
            for page_number, page in enumerate(reader.pages, start=1)
        ]
    except DocumentLoadError:
        raise
    except Exception as exc:
        raise DocumentLoadError(f"Could not read PDF source: {source}") from exc


def _load_text(path, source):
    try:
        content = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        raise DocumentLoadError(f"Could not read UTF-8 source document: {source}") from exc
    return [Document(page_content=content, metadata={"source": source})]
