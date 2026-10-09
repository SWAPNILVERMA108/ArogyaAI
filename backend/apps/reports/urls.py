from django.urls import path

from .views import MedicalReportCollectionView, MedicalReportDetailView, MedicalReportProcessView


app_name = "reports"

urlpatterns = [
    path("upload/", MedicalReportCollectionView.as_view(), name="upload"),
    path("<int:pk>/process/", MedicalReportProcessView.as_view(), name="process"),
    path("<int:pk>/", MedicalReportDetailView.as_view(), name="detail"),
]
