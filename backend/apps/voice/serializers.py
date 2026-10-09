from rest_framework import serializers


LANGUAGE_CHOICES = (("en", "English"), ("hi", "Hindi"))
MAX_AUDIO_BYTES = 10 * 1024 * 1024
ALLOWED_AUDIO_TYPES = {
    "audio/webm", "audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3",
    "audio/mp4", "audio/ogg", "audio/flac", "audio/aac",
}


class VoiceTranscriptionSerializer(serializers.Serializer):
    audio = serializers.FileField()
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, default="en")
    consent_to_cloud_processing = serializers.BooleanField()

    def validate_audio(self, audio):
        if audio.size > MAX_AUDIO_BYTES:
            raise serializers.ValidationError("Audio must be 10 MB or smaller.")
        content_type = (getattr(audio, "content_type", "") or "").lower()
        if content_type not in ALLOWED_AUDIO_TYPES:
            raise serializers.ValidationError(
                "Unsupported audio format. Use WebM, WAV, MP3, MP4, OGG, FLAC, or AAC."
            )
        return audio

    def validate_consent_to_cloud_processing(self, consent):
        if not consent:
            raise serializers.ValidationError(
                "Consent is required because audio is processed by Google Gemini."
            )
        return consent


class VoiceSpeechSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=3000, trim_whitespace=True)
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, default="en")
