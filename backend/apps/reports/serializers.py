from pathlib import Path

from rest_framework import serializers

from .models import MedicalReport, ReportAnalysis


MAX_REPORT_UPLOAD_SIZE = 10 * 1024 * 1024
ALLOWED_FILE_TYPES = {
    ".pdf": (MedicalReport.FileType.PDF, "application/pdf"),
    ".png": (MedicalReport.FileType.PNG, "image/png"),
    ".jpg": (MedicalReport.FileType.JPG, "image/jpeg"),
    ".jpeg": (MedicalReport.FileType.JPG, "image/jpeg"),
}


class ReportAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportAnalysis
        fields = (
            "status",
            "extracted_text",
            "summary",
            "important_values",
            "error_message",
            "updated_at",
        )
        read_only_fields = fields


class MedicalReportSerializer(serializers.ModelSerializer):
    analysis = ReportAnalysisSerializer(read_only=True)

    class Meta:
        model = MedicalReport
        fields = (
            "id",
            "original_filename",
            "file_type",
            "file_size",
            "uploaded_at",
            "analysis",
        )
        read_only_fields = fields


class MedicalReportUploadSerializer(serializers.Serializer):
    file = serializers.FileField(write_only=True)

    def validate_file(self, uploaded_file):
        filename = Path(uploaded_file.name).name
        extension = Path(filename).suffix.casefold()
        if extension not in ALLOWED_FILE_TYPES:
            raise serializers.ValidationError("Only PDF, PNG, JPG, and JPEG files are allowed.")
        if uploaded_file.size > MAX_REPORT_UPLOAD_SIZE:
            raise serializers.ValidationError("The uploaded file cannot exceed 10 MB.")
        if uploaded_file.size == 0:
            raise serializers.ValidationError("The uploaded file is empty.")

        uploaded_file.seek(0)
        signature = uploaded_file.read(8)
        uploaded_file.seek(0)
        if not _signature_matches(extension, signature):
            raise serializers.ValidationError("The file content does not match its extension.")

        file_type, _content_type = ALLOWED_FILE_TYPES[extension]
        uploaded_file.report_file_type = file_type
        uploaded_file.report_original_filename = filename[:255]
        return uploaded_file


def _signature_matches(extension, signature):
    if extension == ".pdf":
        return signature.startswith(b"%PDF-")
    if extension == ".png":
        return signature.startswith(b"\x89PNG\r\n\x1a\n")
    if extension in {".jpg", ".jpeg"}:
        return signature.startswith(b"\xff\xd8\xff")
    return False
