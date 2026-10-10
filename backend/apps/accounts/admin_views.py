from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from common.utils.responses import success_response

from .models import User
from .permissions import IsAdmin
from .serializers import AdminUserSerializer, AdminUserUpdateSerializer

MAX_PAGE_SIZE = 100


class AdminUserListView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(tags=["Admin"], request=None, responses={200: AdminUserSerializer(many=True)})
    def get(self, request):
        users = User.objects.all()
        role = request.query_params.get("role")
        if role in User.Role.values:
            users = users.filter(role=role)
        search = request.query_params.get("search", "").strip()
        if search:
            users = users.filter(Q(name__icontains=search) | Q(email__icontains=search))
        try:
            limit = min(max(int(request.query_params.get("limit", 50)), 1), MAX_PAGE_SIZE)
        except ValueError:
            limit = 50
        return success_response(AdminUserSerializer(users[:limit], many=True).data, "Users retrieved successfully.")


class AdminUserDetailView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(tags=["Admin"], request=AdminUserUpdateSerializer, responses={200: AdminUserSerializer})
    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        serializer = AdminUserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if user.pk == request.user.pk:
            raise PermissionDenied("Administrators cannot change their own role or active status.")
        for field, value in serializer.validated_data.items():
            setattr(user, field, value)
        user.save(update_fields=[*serializer.validated_data.keys(), "updated_at"])
        return success_response(AdminUserSerializer(user).data, "User updated successfully.")


class AdminStatsView(APIView):
    """Aggregate counts only; no private health content is exposed to admins here."""

    permission_classes = [IsAdmin]

    @extend_schema(tags=["Admin"], request=None, responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        from apps.chat.models import Conversation
        from apps.medicines.models import Medicine
        from apps.reports.models import MedicalReport

        data = {
            "users_total": User.objects.count(),
            "users_by_role": {role: User.objects.filter(role=role).count() for role in User.Role.values},
            "inactive_users": User.objects.filter(is_active=False).count(),
            "conversations": Conversation.objects.count(),
            "reports": MedicalReport.objects.count(),
            "medicines": Medicine.objects.count(),
        }
        return success_response(data, "Statistics retrieved successfully.")
