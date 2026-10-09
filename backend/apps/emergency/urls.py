from django.urls import path

from .views import (
    EmergencyContactCollectionView,
    EmergencyContactDetailView,
    EmergencyInfoView,
    LocationShareView,
)


app_name = "emergency"

urlpatterns = [
    path("info/", EmergencyInfoView.as_view(), name="info"),
    path("contacts/", EmergencyContactCollectionView.as_view(), name="contacts"),
    path("contacts/<int:pk>/", EmergencyContactDetailView.as_view(), name="contact-detail"),
    path("location-share/", LocationShareView.as_view(), name="location-share"),
]
