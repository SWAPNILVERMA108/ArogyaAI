from django.urls import path

from .views import SpeechView, TranscriptionView


app_name = "voice"

urlpatterns = [
    path("transcribe/", TranscriptionView.as_view(), name="transcribe"),
    path("speak/", SpeechView.as_view(), name="speak"),
]
