from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class IsPatientOrAdmin(BasePermission):
    message = "Only patients or administrators may manage patient profiles."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.Role.PATIENT, User.Role.ADMIN)
        )

    def has_object_permission(self, request, view, obj):
        return request.user.role == User.Role.ADMIN or obj.user_id == request.user.id
