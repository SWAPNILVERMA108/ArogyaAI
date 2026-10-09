import logging
import os

from django.http import HttpResponse
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from ai.llm.gemini import LLMConfigurationError, LLMProviderError
from ai.voice.service import VoiceService
from common.exceptions.api import ServiceUnavailable
from common.utils.responses import success_response

from .serializers import VoiceSpeechSerializer, VoiceTranscriptionSerializer


logger = logging.getLogger(__name__)


def _service_unavailable(exc):
    logger.warning("Voice processing failed (%s).", type(exc).__name__)
    raise ServiceUnavailable(
        "Voice processing is unavailable. Check server configuration and try again."
    ) from exc


class TranscriptionView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "voice"

    @extend_schema(tags=["Voice"], request=VoiceTranscriptionSerializer, responses={200: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = VoiceTranscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if os.environ.get("VOICE_CLOUD_ENABLED", "False").strip().lower() not in {"1", "true", "yes"}:
            raise ServiceUnavailable("Cloud voice processing is disabled by the server.")
        try:
            transcript = VoiceService().transcribe(
                serializer.validated_data["audio"], serializer.validated_data["language"]
            )
        except (LLMConfigurationError, LLMProviderError) as exc:
            _service_unavailable(exc)
        return success_response({
            "transcript": transcript,
            "language": serializer.validated_data["language"],
        }, "Audio transcribed successfully.")


class SpeechView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "voice"

    @extend_schema(tags=["Voice"], request=VoiceSpeechSerializer, responses={200: OpenApiTypes.BINARY})
    def post(self, request):
        serializer = VoiceSpeechSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if os.environ.get("VOICE_CLOUD_ENABLED", "False").strip().lower() not in {"1", "true", "yes"}:
            raise ServiceUnavailable("Cloud voice processing is disabled by the server.")
        try:
            audio = VoiceService().speak(
                serializer.validated_data["text"], serializer.validated_data["language"]
            )
        except (LLMConfigurationError, LLMProviderError) as exc:
            _service_unavailable(exc)
        response = HttpResponse(audio, content_type="audio/wav")
        response["Content-Disposition"] = 'inline; filename="arogyaai-response.wav"'
        response["Cache-Control"] = "no-store"
        return response
