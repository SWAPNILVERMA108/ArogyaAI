"""Gemini-backed speech recognition and speech synthesis."""

import base64
import json
import logging
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ai.llm.gemini import LLMConfigurationError, LLMProviderError


logger = logging.getLogger(__name__)
LANGUAGE_CODES = {"en": "en-IN", "hi": "hi-IN"}


class VoiceService:
    """Process voice in memory; audio is never persisted by this service."""

    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.timeout = float(os.environ.get("GEMINI_TIMEOUT_SECONDS", "20"))

    def _ensure_enabled(self):
        if os.environ.get("VOICE_CLOUD_ENABLED", "False").strip().lower() not in {"1", "true", "yes"}:
            raise LLMConfigurationError("Cloud voice processing is not enabled.")
        if not self.api_key:
            raise LLMConfigurationError("GEMINI_API_KEY is not configured.")

    def _post_json(self, endpoint, payload):
        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            logger.warning("Gemini voice request failed with HTTP status %s.", exc.code)
            raise LLMProviderError("The voice provider request failed.") from exc
        except (URLError, TimeoutError, OSError) as exc:
            logger.warning("Gemini voice provider could not be reached.")
            raise LLMProviderError("The voice provider is unreachable.") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            logger.warning("Gemini voice provider returned invalid data.")
            raise LLMProviderError("The voice provider returned invalid data.") from exc

    def transcribe(self, audio, language):
        self._ensure_enabled()
        audio_type = (getattr(audio, "content_type", "") or "audio/webm").lower()
        audio_data = audio.read()
        if not audio_data:
            raise LLMProviderError("The audio recording is empty.")
        model = os.environ.get("GEMINI_STT_MODEL", "gemini-3.5-flash").strip()
        language_name = {"en": "English", "hi": "Hindi"}[language]
        prompt = (
            f"Transcribe this audio verbatim in {language_name}. Do not translate, "
            "summarize, interpret, or answer it. Return only the spoken words."
        )
        result = self._post_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            {
                "contents": [{"role": "user", "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": audio_type, "data": base64.b64encode(audio_data).decode("ascii")}},
                ]}],
                "generationConfig": {"temperature": 0, "maxOutputTokens": 1024},
            },
        )
        parts = ((result.get("candidates") or [{}])[0].get("content") or {}).get("parts") or []
        transcript = " ".join(
            part["text"].strip() for part in parts
            if isinstance(part, dict) and isinstance(part.get("text"), str) and part["text"].strip()
        ).strip()
        if not transcript:
            raise LLMProviderError("The voice provider returned no transcription.")
        return transcript

    def speak(self, text, language):
        self._ensure_enabled()
        model = os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts").strip()
        voice = os.environ.get("GEMINI_TTS_VOICE", "Kore").strip()
        result = self._post_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            {
                "contents": [{"parts": [{"text": text}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}},
                        "languageCode": LANGUAGE_CODES[language],
                    },
                },
            },
        )
        parts = ((result.get("candidates") or [{}])[0].get("content") or {}).get("parts") or []
        for part in parts:
            inline_data = part.get("inlineData") or part.get("inline_data") or {}
            encoded = inline_data.get("data")
            if encoded:
                try:
                    audio = base64.b64decode(encoded, validate=True)
                except (ValueError, TypeError) as exc:
                    raise LLMProviderError("The voice provider returned invalid audio.") from exc
                if audio:
                    return audio
        raise LLMProviderError("The voice provider returned no audio.")
