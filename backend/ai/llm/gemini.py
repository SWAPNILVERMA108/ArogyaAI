import json
import logging
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


logger = logging.getLogger(__name__)


class LLMConfigurationError(Exception):
    """Raised when the configured model provider cannot be initialized."""


class LLMProviderError(Exception):
    """Raised when a model provider request fails or returns no usable text."""


class GeminiClient:
    """Small REST client for Gemini GenerateContent using stdlib networking."""

    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash").strip()
        try:
            self.timeout = float(os.environ.get("GEMINI_TIMEOUT_SECONDS", "20"))
        except ValueError as exc:
            raise LLMConfigurationError("GEMINI_TIMEOUT_SECONDS must be numeric.") from exc

    def generate(self, contents, system_instruction):
        if not self.api_key:
            raise LLMConfigurationError("GEMINI_API_KEY is not configured.")
        if not self.model:
            raise LLMConfigurationError("GEMINI_MODEL is not configured.")

        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
            },
        }
        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            logger.warning("Gemini request failed with HTTP status %s.", exc.code)
            raise LLMProviderError("The configured language model request failed.") from exc
        except (URLError, TimeoutError, OSError) as exc:
            logger.warning("Gemini request could not reach the provider.")
            raise LLMProviderError("The configured language model is unreachable.") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            logger.warning("Gemini returned an invalid response body.")
            raise LLMProviderError("The configured language model returned invalid data.") from exc

        candidates = result.get("candidates") if isinstance(result, dict) else None
        if not isinstance(candidates, list) or not candidates:
            logger.warning("Gemini returned no response candidates.")
            raise LLMProviderError("The configured language model returned no response.")

        candidate = candidates[0]
        candidate_content = candidate.get("content") if isinstance(candidate, dict) else None
        parts = candidate_content.get("parts") if isinstance(candidate_content, dict) else None
        if not isinstance(parts, list):
            logger.warning("Gemini returned a response without text parts.")
            raise LLMProviderError("The configured language model returned no text.")
        answer = "".join(
            part.get("text", "")
            for part in parts
            if isinstance(part, dict) and isinstance(part.get("text", ""), str)
        ).strip()
        if not answer:
            logger.warning("Gemini returned an empty text response.")
            raise LLMProviderError("The configured language model returned no text.")
        return answer
