import uuid
from pathlib import Path

from django.conf import settings
from django.db import models


def report_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"reports/user_{instance.user_id}/{uuid.uuid4().hex}{suffix}"


class MedicalReport(models.Model):
    class FileType(models.TextChoices):
        PDF = "PDF", "PDF"
        PNG = "PNG", "PNG image"
        JPG = "JPG", "JPEG image"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="medical_reports",
    )
    patient = models.ForeignKey(
        "patients.PatientProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medical_reports",
    )
    file = models.FileField(upload_to=report_upload_path, max_length=255)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=4, choices=FileType.choices)
    file_size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at", "-id"]

    def __str__(self):
        return f"{self.file_type} report for {self.user.email}"


class ReportAnalysis(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending OCR"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    report = models.OneToOneField(
        MedicalReport,
        on_delete=models.CASCADE,
        related_name="analysis",
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    extracted_text = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    important_values = models.JSONField(default=list, blank=True)
    error_message = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analysis for report {self.report_id}: {self.status}"
