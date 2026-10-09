from rest_framework.permissions import BasePermission

from .models import User


class HasRole(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in self.allowed_roles
        )


class IsPatient(HasRole):
    allowed_roles = (User.Role.PATIENT,)


class IsDoctor(HasRole):
    allowed_roles = (User.Role.DOCTOR,)


class IsAdmin(HasRole):
    allowed_roles = (User.Role.ADMIN,)
