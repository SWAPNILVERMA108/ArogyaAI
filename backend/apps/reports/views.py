from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from common.utils.responses import success_response
from common.exceptions.api import ServiceUnavailable
from ai.ocr.service import OCRDocumentError, OCREngineUnavailable

from .models import MedicalReport
from .exceptions import ReportProcessingError
from .permissions import IsPatient
from .serializers import MedicalReportSerializer, MedicalReportUploadSerializer
from .services import MedicalReportService


class MedicalReportCollectionView(APIView):
    permission_classes = [IsPatient]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=["Reports"],
        request=MedicalReportUploadSerializer,
        responses={201: MedicalReportSerializer},
    )
    def post(self, request):
        serializer = MedicalReportUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = MedicalReportService.create_report(
            request.user,
            serializer.validated_data["file"],
        )
        return success_response(
            MedicalReportSerializer(report).data,
            "Report uploaded successfully. OCR processing is pending.",
            status.HTTP_201_CREATED,
        )

    @extend_schema(tags=["Reports"], request=None, responses={200: MedicalReportSerializer(many=True)})
    def get(self, request):
        reports = MedicalReport.objects.filter(user=request.user).select_related("analysis")
        return success_response(MedicalReportSerializer(reports, many=True).data, "Reports retrieved successfully.")


class MedicalReportDetailView(APIView):
    permission_classes = [IsPatient]

    def get_report(self, request, pk):
        return get_object_or_404(
            MedicalReport.objects.select_related("analysis"),
            pk=pk,
            user=request.user,
        )

    @extend_schema(tags=["Reports"], request=None, responses={200: MedicalReportSerializer})
    def get(self, request, pk):
        report = self.get_report(request, pk)
        return success_response(MedicalReportSerializer(report).data, "Report retrieved successfully.")

    @extend_schema(tags=["Reports"], request=None, responses={200: OpenApiTypes.OBJECT})
    def delete(self, request, pk):
        report = self.get_report(request, pk)
        MedicalReportService.delete_report(report)
        return success_response(None, "Report deleted successfully.")


class MedicalReportProcessView(APIView):
    permission_classes = [IsPatient]

    @extend_schema(tags=["Reports"], request=None, responses={200: MedicalReportSerializer})
    def post(self, request, pk):
        report = get_object_or_404(
            MedicalReport.objects.select_related("analysis"),
            pk=pk,
            user=request.user,
        )
        try:
            MedicalReportService.process_report(report)
        except OCREngineUnavailable as exc:
            raise ServiceUnavailable(
                "OCR is temporarily unavailable. Please contact the administrator."
            ) from exc
        except OCRDocumentError as exc:
            raise ReportProcessingError(
                "The report could not be processed. Please check the file and try again."
            ) from exc
        report.refresh_from_db()
        return success_response(
            MedicalReportSerializer(report).data,
            "Text extraction completed. This output is not a medical diagnosis.",
        )
