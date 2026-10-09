from rest_framework.response import Response


def success_response(data, message, status=200):
    return Response({"success": True, "data": data, "message": message}, status=status)
