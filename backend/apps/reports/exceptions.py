from rest_framework import status
from rest_framework.exceptions import APIException


class ReportProcessingError(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_code = "report_ocr_failed"
    default_detail = "The uploaded report could not be processed."
