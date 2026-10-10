from django.urls import path

from .views import (
    AccessGrantCollectionView,
    AccessGrantDetailView,
    MyPatientProfileView,
    PatientProfileCollectionView,
    PatientProfileDetailView,
)


app_name = "patients"

urlpatterns = [
    path("", PatientProfileCollectionView.as_view(), name="create"),
    path("me/", MyPatientProfileView.as_view(), name="me"),
    path("access/", AccessGrantCollectionView.as_view(), name="access"),
    path("access/<int:pk>/", AccessGrantDetailView.as_view(), name="access-detail"),
    path("<int:pk>/", PatientProfileDetailView.as_view(), name="detail"),
]
