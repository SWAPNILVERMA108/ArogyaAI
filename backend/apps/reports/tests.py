from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import MedicalReport, ReportAnalysis


User = get_user_model()


class MedicalReportAPITests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            email="report-patient@example.com", name="Report Patient", password="StrongPass123!"
        )
        self.other_patient = User.objects.create_user(
            email="report-other@example.com", name="Other Patient", password="StrongPass123!"
        )
        self.client.force_authenticate(self.patient)

    @staticmethod
    def pdf_file(name="lab-result.pdf", content=b"%PDF-1.7\nTest fixture"):
        return SimpleUploadedFile(name, content, content_type="application/pdf")

    def test_upload_stores_private_metadata_and_pending_analysis(self):
        response = self.client.post(
            reverse("reports:upload"), {"file": self.pdf_file()}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report = MedicalReport.objects.get(pk=response.data["data"]["id"])
        self.assertEqual(report.user, self.patient)
        self.assertEqual(report.original_filename, "lab-result.pdf")
        self.assertEqual(report.file_type, MedicalReport.FileType.PDF)
        self.assertTrue(report.file.name.startswith(f"reports/user_{self.patient.id}/"))
        self.assertNotIn("file", response.data["data"])
        self.assertEqual(report.analysis.status, ReportAnalysis.Status.PENDING)
        self.assertEqual(report.analysis.summary, "")

    def test_user_can_list_and_retrieve_only_own_reports(self):
        own = self.client.post(reverse("reports:upload"), {"file": self.pdf_file()}, format="multipart")
        own_id = own.data["data"]["id"]

        listed = self.client.get(reverse("reports:upload"))
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in listed.data["data"]], [own_id])

        self.client.force_authenticate(self.other_patient)
        detail = self.client.get(reverse("reports:detail", args=[own_id]))
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

        process = self.client.post(reverse("reports:process", args=[own_id]))
        self.assertEqual(process.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_extension_and_mismatched_signature_are_rejected(self):
        invalid_extension = self.client.post(
            reverse("reports:upload"),
            {"file": SimpleUploadedFile("notes.txt", b"not allowed")},
            format="multipart",
        )
        self.assertEqual(invalid_extension.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_signature = self.client.post(
            reverse("reports:upload"),
            {"file": SimpleUploadedFile("fake.pdf", b"not a pdf")},
            format="multipart",
        )
        self.assertEqual(invalid_signature.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(MedicalReport.objects.count(), 0)

    def test_png_and_jpeg_uploads_are_accepted(self):
        for filename, signature in (
            ("scan.png", b"\x89PNG\r\n\x1a\n"),
            ("photo.jpeg", b"\xff\xd8\xff\xe0\x00\x10JFIF"),
        ):
            with self.subTest(filename=filename):
                response = self.client.post(
                    reverse("reports:upload"),
                    {"file": SimpleUploadedFile(filename, signature)},
                    format="multipart",
                )
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_oversize_and_empty_uploads_are_rejected(self):
        too_large = SimpleUploadedFile("large.pdf", BytesIO(b"%PDF-1.7" + b"x" * (10 * 1024 * 1024)).getvalue())
        large_response = self.client.post(
            reverse("reports:upload"), {"file": too_large}, format="multipart"
        )
        empty_response = self.client.post(
            reverse("reports:upload"), {"file": SimpleUploadedFile("empty.pdf", b"")}, format="multipart"
        )
        self.assertEqual(large_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(empty_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_anonymous_and_non_patient_users_are_denied(self):
        self.client.force_authenticate(user=None)
        anonymous = self.client.get(reverse("reports:upload"))
        self.assertEqual(anonymous.status_code, status.HTTP_401_UNAUTHORIZED)

        doctor = User.objects.create_user(
            email="report-doctor@example.com",
            name="Doctor",
            password="StrongPass123!",
            role=User.Role.DOCTOR,
        )
        self.client.force_authenticate(doctor)
        denied = self.client.get(reverse("reports:upload"))
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_removes_record_and_stored_file(self):
        response = self.client.post(
            reverse("reports:upload"), {"file": self.pdf_file()}, format="multipart"
        )
        report = MedicalReport.objects.get(pk=response.data["data"]["id"])
        self.assertTrue(report.file.storage.exists(report.file.name))

        deleted = self.client.delete(reverse("reports:detail", args=[report.pk]))

        self.assertEqual(deleted.status_code, status.HTTP_200_OK)
        self.assertFalse(MedicalReport.objects.filter(pk=report.pk).exists())
        self.assertFalse(report.file.storage.exists(report.file.name))

    @patch("ai.ocr.service.OCRService.extract", return_value="[Page 1]\nHemoglobin: 12 g/dL")
    def test_patient_can_process_report_and_get_extracted_text(self, extract):
        uploaded = self.client.post(
            reverse("reports:upload"), {"file": self.pdf_file()}, format="multipart"
        )
        report_id = uploaded.data["data"]["id"]

        response = self.client.post(reverse("reports:process", args=[report_id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["analysis"]["status"], "COMPLETED")
        self.assertEqual(
            response.data["data"]["analysis"]["extracted_text"],
            "[Page 1]\nHemoglobin: 12 g/dL",
        )
        self.assertEqual(response.data["data"]["analysis"]["summary"], "")
        self.assertIn("not a medical diagnosis", response.data["message"])
        extract.assert_called_once()

    def test_report_processing_fails_safely_and_does_not_expose_internal_errors(self):
        uploaded = self.client.post(
            reverse("reports:upload"), {"file": self.pdf_file()}, format="multipart"
        )
        report_id = uploaded.data["data"]["id"]

        from ai.ocr.service import OCREngineUnavailable

        with patch(
            "apps.reports.services.OCRService.extract",
            side_effect=OCREngineUnavailable("tesseract path details"),
        ):
            response = self.client.post(reverse("reports:process", args=[report_id]))

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        report = MedicalReport.objects.get(pk=report_id)
        self.assertEqual(report.analysis.status, ReportAnalysis.Status.FAILED)
        self.assertNotIn("tesseract path details", str(response.data))

    @patch("ai.ocr.service.subprocess.run")
    def test_tesseract_receives_image_bytes_without_shell_interpolation(self, run):
        from ai.ocr.service import OCRService

        run.return_value = SimpleNamespace(returncode=0, stdout="recognized words".encode())
        with patch.dict("os.environ", {"TESSERACT_CMD": "tesseract", "TESSERACT_LANGUAGES": "eng"}):
            text = OCRService._run_tesseract(b"image bytes", timeout_seconds=5)

        self.assertEqual(text, "recognized words")
        self.assertEqual(run.call_args.args[0], ["tesseract", "stdin", "stdout", "-l", "eng", "--psm", "6"])
        self.assertEqual(run.call_args.kwargs["input"], b"image bytes")
        self.assertEqual(run.call_args.kwargs["timeout"], 5)

    @patch("ai.ocr.service.PdfReader")
    def test_digital_pdf_text_is_extracted_without_tesseract(self, pdf_reader):
        from ai.ocr.service import OCRService

        pdf_reader.return_value = SimpleNamespace(
            is_encrypted=False,
            pages=[SimpleNamespace(extract_text=lambda: "A digitally readable lab result.")],
        )

        text = OCRService.extract_pdf(b"pdf fixture")

        self.assertEqual(text, "[Page 1]\nA digitally readable lab result.")

    @patch("ai.ocr.service.OCRService._run_tesseract", return_value="scanned page text")
    def test_scanned_pdf_pages_are_rendered_and_ocr_is_used(self, run_ocr):
        import pymupdf

        from ai.ocr.service import OCRService

        document = pymupdf.open()
        document.new_page()
        content = document.tobytes()
        document.close()

        text = OCRService.extract_pdf(content)

        self.assertEqual(text, "[Page 1]\nscanned page text")
        run_ocr.assert_called_once()
        self.assertEqual(run_ocr.call_args.args[1], 60)
