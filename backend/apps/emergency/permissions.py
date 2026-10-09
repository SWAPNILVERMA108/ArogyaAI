from rest_framework.permissions import BasePermission


class IsPatient(BasePermission):
    message = "Only patient accounts may manage personal emergency contacts."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "PATIENT"
        )
