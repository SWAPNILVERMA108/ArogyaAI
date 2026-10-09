from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class IsPatient(BasePermission):
    message = "Only patient accounts may manage personal medicines."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.PATIENT
        )
