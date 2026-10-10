from django.urls import path

from .doctor_views import DoctorPatientDetailView, DoctorPatientListView

app_name = "doctor"

urlpatterns = [
    path("patients/", DoctorPatientListView.as_view(), name="patients"),
    path("patients/<int:patient_id>/", DoctorPatientDetailView.as_view(), name="patient-detail"),
]
