from django.db import transaction
from django.utils import timezone

from ai.ocr.service import OCRDocumentError, OCREngineUnavailable, OCRService
from apps.patients.models import PatientProfile

from .models import MedicalReport, ReportAnalysis


class MedicalReportService:
    @staticmethod
    def create_report(user, uploaded_file):
        report = None
        try:
            with transaction.atomic():
                patient = PatientProfile.objects.filter(user=user).first()
                report = MedicalReport.objects.create(
                    user=user,
                    patient=patient,
                    file=uploaded_file,
                    original_filename=uploaded_file.report_original_filename,
                    file_type=uploaded_file.report_file_type,
                    file_size=uploaded_file.size,
                )
                ReportAnalysis.objects.create(report=report)
        except Exception:
            if report and report.file:
                report.file.delete(save=False)
            raise
        return report

    @staticmethod
    def delete_report(report):
        stored_file = report.file
        report.delete()
        if stored_file:
            stored_file.delete(save=False)

    @staticmethod
    def process_report(report):
        analysis = report.analysis
        try:
            extracted_text = OCRService.extract(report)
        except OCREngineUnavailable:
            analysis.status = ReportAnalysis.Status.FAILED
            analysis.error_message = "OCR is not configured. Contact the administrator."
            analysis.updated_at = timezone.now()
            analysis.save(update_fields=["status", "error_message", "updated_at"])
            raise
        except OCRDocumentError:
            analysis.status = ReportAnalysis.Status.FAILED
            analysis.error_message = "The uploaded report could not be processed."
            analysis.updated_at = timezone.now()
            analysis.save(update_fields=["status", "error_message", "updated_at"])
            raise

        analysis.status = ReportAnalysis.Status.COMPLETED
        analysis.extracted_text = extracted_text
        analysis.summary = ""
        analysis.error_message = ""
        analysis.updated_at = timezone.now()
        analysis.save(
            update_fields=[
                "status",
                "extracted_text",
                "summary",
                "error_message",
                "updated_at",
            ]
        )
        return analysis
