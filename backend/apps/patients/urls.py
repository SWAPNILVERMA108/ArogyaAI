from django.urls import path

from .views import MyPatientProfileView, PatientProfileCollectionView, PatientProfileDetailView


app_name = "patients"

urlpatterns = [
    path("", PatientProfileCollectionView.as_view(), name="create"),
    path("me/", MyPatientProfileView.as_view(), name="me"),
    path("<int:pk>/", PatientProfileDetailView.as_view(), name="detail"),
]
