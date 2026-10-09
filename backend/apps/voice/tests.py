import base64
import io
import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase

from ai.voice.service import VoiceService


User = get_user_model()


class VoiceServiceTests(APITestCase):
    @patch.dict(os.environ, {"VOICE_CLOUD_ENABLED": "True", "GEMINI_API_KEY": "test-key"})
    @patch.object(VoiceService, "_post_json")
    def test_transcription_sends_inline_audio_and_returns_text(self, post_json):
        post_json.return_value = {"candidates": [{"content": {"parts": [{"text": "Namaste"}]}}]}
        audio = io.BytesIO(b"fake-webm")
        audio.content_type = "audio/webm"

        transcript = VoiceService().transcribe(audio, "hi")

        self.assertEqual(transcript, "Namaste")
        payload = post_json.call_args.args[1]
        self.assertIn("Hindi", payload["contents"][0]["parts"][0]["text"])
        encoded = payload["contents"][0]["parts"][1]["inline_data"]["data"]
        self.assertEqual(base64.b64decode(encoded), b"fake-webm")

    @patch.dict(os.environ, {"VOICE_CLOUD_ENABLED": "True", "GEMINI_API_KEY": "test-key"})
    @patch.object(VoiceService, "_post_json")
    def test_speech_returns_decoded_audio_and_uses_requested_language(self, post_json):
        wav = b"RIFF\x00\x00\x00\x00WAVE"
        post_json.return_value = {"candidates": [{"content": {"parts": [
            {"inlineData": {"data": base64.b64encode(wav).decode("ascii")}}
        ]}}]}

        audio = VoiceService().speak("Hello", "en")

        self.assertEqual(audio, wav)
        payload = post_json.call_args.args[1]
        self.assertEqual(payload["generationConfig"]["speechConfig"]["languageCode"], "en-IN")


class VoiceAPITests(APITestCase):
    def setUp(self):
        user = User.objects.create_user(
            email="voice-user@example.com", name="Voice User", password="StrongPass123!"
        )
        self.client.force_authenticate(user)

    @patch.dict(os.environ, {"VOICE_CLOUD_ENABLED": "True", "GEMINI_API_KEY": "test-key"})
    @patch("ai.voice.service.VoiceService.transcribe", return_value="I have a headache.")
    def test_transcribe_requires_consent_and_returns_text(self, transcribe):
        url = reverse("voice:transcribe")
        no_consent = self.client.post(url, {
            "audio": SimpleUploadedFile("recording.webm", b"audio", content_type="audio/webm"),
            "language": "en",
            "consent_to_cloud_processing": "false",
        }, format="multipart")
        self.assertEqual(no_consent.status_code, 400)

        response = self.client.post(url, {
            "audio": SimpleUploadedFile("recording.webm", b"audio", content_type="audio/webm"),
            "language": "en",
            "consent_to_cloud_processing": "true",
        }, format="multipart")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["data"]["transcript"], "I have a headache.")
        transcribe.assert_called_once()

    @patch.dict(os.environ, {"VOICE_CLOUD_ENABLED": "True", "GEMINI_API_KEY": "test-key"})
    @patch("ai.voice.service.VoiceService.speak", return_value=b"RIFFwave")
    def test_speak_returns_uncached_wav(self, speak):
        response = self.client.post(reverse("voice:speak"), {
            "text": "Hello", "language": "hi",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "audio/wav")
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(response.content, b"RIFFwave")
        speak.assert_called_once_with("Hello", "hi")

    @patch.dict(os.environ, {"VOICE_CLOUD_ENABLED": "False"})
    def test_cloud_voice_disabled_by_default(self):
        response = self.client.post(reverse("voice:speak"), {
            "text": "Hello", "language": "en",
        }, format="json")
        self.assertEqual(response.status_code, 503)

    def test_transcription_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(reverse("voice:transcribe"), {}, format="multipart")
        self.assertEqual(response.status_code, 401)
