from rest_framework.permissions import BasePermission


class IsConversationOwner(BasePermission):
    message = "You do not have access to this conversation."

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id
