from django.urls import path

from .views import (
    MarkMedicineTakenView,
    MedicationLogListView,
    MedicineCollectionView,
    MedicineDetailView,
    ReminderCollectionView,
    ReminderDetailView,
)


app_name = "medicines"

urlpatterns = [
    path("", MedicineCollectionView.as_view(), name="list-create"),
    path("<int:pk>/", MedicineDetailView.as_view(), name="detail"),
    path("<int:pk>/reminders/", ReminderCollectionView.as_view(), name="reminders"),
    path("<int:pk>/reminders/<int:reminder_id>/", ReminderDetailView.as_view(), name="reminder-detail"),
    path("<int:pk>/taken/", MarkMedicineTakenView.as_view(), name="taken"),
    path("<int:pk>/logs/", MedicationLogListView.as_view(), name="logs"),
]
