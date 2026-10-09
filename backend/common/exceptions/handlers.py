from rest_framework.exceptions import ErrorDetail
from rest_framework.views import exception_handler


def _message_from_data(data):
    if isinstance(data, dict):
        detail = data.get("detail")
        if detail:
            return str(detail)
        first_value = next(iter(data.values()), "Request could not be processed.")
        if isinstance(first_value, list) and first_value:
            return str(first_value[0])
        return str(first_value)
    if isinstance(data, list) and data:
        return str(data[0])
    return "Request could not be processed."


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    detail = response.data
    code = "validation_error" if response.status_code == 400 else "request_error"
    if isinstance(detail, dict) and isinstance(detail.get("detail"), ErrorDetail):
        code = detail["detail"].code

    response.data = {
        "success": False,
        "error": {
            "code": code,
            "message": _message_from_data(detail),
            "details": detail,
        },
    }
    return response
