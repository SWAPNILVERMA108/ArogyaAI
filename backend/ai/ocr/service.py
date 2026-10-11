import base64
import json
import logging
import os
import subprocess
import time
from io import BytesIO
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pypdf import PdfReader


MAX_PDF_PAGES = 30
MAX_PDF_PAGE_PIXELS = 20_000_000
MAX_OCR_SECONDS = 120
MAX_IMAGE_OCR_SECONDS = 30

logger = logging.getLogger(__name__)
OCR_PROMPT = (
    "Transcribe all the text visible in this image exactly as written, line by line. "
    "Do not explain, summarise, correct or interpret it, and do not add anything. "
    "If a word is unreadable write [unclear]. If there is no text, reply with nothing."
)


class OCRError(Exception):
    """Base exception for local report text extraction."""


class OCREngineUnavailable(OCRError):
    """Tesseract is not installed or cannot be started."""


class OCRDocumentError(OCRError):
    """The report is unreadable or exceeds safe OCR limits."""


class OCRService:
    @classmethod
    def extract(cls, report):
        try:
            with report.file.open("rb") as source:
                content = source.read()
        except OSError as exc:
            raise OCRDocumentError("The stored report could not be read.") from exc

        if report.file_type == "PDF":
            return cls.extract_pdf(content)
        if report.file_type in {"PNG", "JPG"}:
            mime = "image/png" if report.file_type == "PNG" else "image/jpeg"
            text = cls._recognise(content, MAX_IMAGE_OCR_SECONDS, mime)
            if not text:
                raise OCRDocumentError("No readable text was found in this report.")
            return text
        raise OCRDocumentError("This report file type is not supported for text extraction.")

    @classmethod
    def extract_pdf(cls, content):
        try:
            reader = PdfReader(BytesIO(content), strict=False)
            if reader.is_encrypted:
                raise OCRDocumentError("Encrypted PDFs cannot be processed.")
            if len(reader.pages) > MAX_PDF_PAGES:
                raise OCRDocumentError(f"PDFs are limited to {MAX_PDF_PAGES} pages for OCR.")
            page_texts = [page.extract_text() or "" for page in reader.pages]
        except OCRDocumentError:
            raise
        except Exception as exc:
            raise OCRDocumentError("The PDF could not be read.") from exc

        pages_needing_ocr = [
            index
            for index, text in enumerate(page_texts)
            if not text.strip()
        ]
        if pages_needing_ocr:
            page_texts = cls._ocr_pdf_pages(content, page_texts, pages_needing_ocr)

        extracted = "\n\n".join(
            f"[Page {index + 1}]\n{text.strip()}"
            for index, text in enumerate(page_texts)
            if text and text.strip()
        )
        if not extracted.strip():
            raise OCRDocumentError("No readable text was found in this report.")
        return extracted

    @classmethod
    def _ocr_pdf_pages(cls, content, page_texts, page_indexes):
        try:
            import pymupdf
        except ImportError as exc:
            raise OCREngineUnavailable(
                "PDF image OCR requires the PyMuPDF dependency. Install backend requirements."
            ) from exc

        try:
            document = pymupdf.open(stream=content, filetype="pdf")
        except Exception as exc:
            raise OCRDocumentError("The PDF pages could not be rendered for OCR.") from exc

        if len(document) != len(page_texts):
            document.close()
            raise OCRDocumentError("The PDF page count could not be verified safely.")

        deadline = time.monotonic() + MAX_OCR_SECONDS
        try:
            for page_index in page_indexes:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise OCRDocumentError("OCR exceeded its 120-second processing limit.")
                try:
                    page = document[page_index]
                    estimated_pixels = (
                        page.rect.width * page.rect.height * (180 / 72) ** 2
                    )
                    if estimated_pixels > MAX_PDF_PAGE_PIXELS:
                        raise OCRDocumentError(
                            "A PDF page exceeds the safe image size for OCR."
                        )
                    pixmap = page.get_pixmap(dpi=180, alpha=False)
                except OCRDocumentError:
                    raise
                except Exception as exc:
                    raise OCRDocumentError("A PDF page could not be rendered for OCR.") from exc
                if pixmap.width * pixmap.height > MAX_PDF_PAGE_PIXELS:
                    raise OCRDocumentError("A PDF page exceeds the safe image size for OCR.")
                page_texts[page_index] = cls._recognise(
                    pixmap.tobytes("png"), min(remaining, 60), "image/png"
                )
        finally:
            document.close()
        return page_texts

    @classmethod
    def _recognise(cls, image_bytes, timeout_seconds, mime_type):
        """OCR_PROVIDER=tesseract (default, runs on the server) or gemini (cloud vision)."""
        provider = os.environ.get("OCR_PROVIDER", "tesseract").strip().lower()
        if provider == "gemini":
            return cls._run_gemini(image_bytes, timeout_seconds, mime_type)
        return cls._run_tesseract(image_bytes, timeout_seconds)

    @staticmethod
    def _run_gemini(image_bytes, timeout_seconds, mime_type):
        # Sends the image to Google, so the operator must opt in explicitly.
        if os.environ.get("OCR_CLOUD_ENABLED", "").strip().lower() not in {"1", "true", "yes"}:
            raise OCREngineUnavailable("Cloud OCR is disabled. Set OCR_CLOUD_ENABLED=True.")
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        model = (os.environ.get("GEMINI_OCR_MODEL") or os.environ.get("GEMINI_MODEL") or "").strip()
        if not api_key or not model:
            raise OCREngineUnavailable("GEMINI_API_KEY and a Gemini model must be configured.")
        payload = {
            "contents": [{"parts": [
                {"text": OCR_PROMPT},
                {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode("ascii")}},
            ]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 4096},
        }
        request = Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            logger.warning("Cloud OCR request failed: %s %s", type(exc).__name__, getattr(exc, "code", ""))
            raise OCREngineUnavailable("The cloud OCR service is unavailable.") from exc
        parts = (((result.get("candidates") or [{}])[0].get("content") or {}).get("parts")) or []
        return "".join(part.get("text", "") for part in parts).strip()

    @staticmethod
    def _run_tesseract(image_bytes, timeout_seconds):
        executable = os.environ.get("TESSERACT_CMD", "tesseract").strip()
        languages = os.environ.get("TESSERACT_LANGUAGES", "eng").strip()
        if not executable or not languages:
            raise OCREngineUnavailable("Configure TESSERACT_CMD and TESSERACT_LANGUAGES.")

        try:
            result = subprocess.run(
                [executable, "stdin", "stdout", "-l", languages, "--psm", "6"],
                input=image_bytes,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise OCREngineUnavailable(
                "Tesseract OCR is not installed or TESSERACT_CMD is not configured."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise OCRDocumentError("OCR exceeded its processing time limit.") from exc
        except OSError as exc:
            raise OCREngineUnavailable("Tesseract OCR could not be started.") from exc

        if result.returncode != 0:
            raise OCREngineUnavailable("Tesseract OCR failed. Check the installed language data.")
        try:
            return result.stdout.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise OCRDocumentError("OCR output could not be decoded as UTF-8.") from exc