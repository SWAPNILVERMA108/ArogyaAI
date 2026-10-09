from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from common.utils.responses import success_response

from .serializers import LoginSerializer, ProfileUpdateSerializer, RefreshSerializer, RegisterSerializer, UserSerializer
from .services import AccountService


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    @extend_schema(
        tags=["Authentication"],
        request=RegisterSerializer,
        responses={201: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AccountService.register_user(serializer.validated_data)
        return success_response(
            {"user": UserSerializer(user).data, "tokens": AccountService.issue_tokens(user)},
            "Account created successfully.",
            status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    @extend_schema(
        tags=["Authentication"],
        request=LoginSerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return success_response(
            {"user": UserSerializer(user).data, "tokens": AccountService.issue_tokens(user)},
            "Login successful.",
        )


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    @extend_schema(
        tags=["Authentication"],
        request=RefreshSerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = AccountService.refresh_tokens(serializer.validated_data["refresh"])
        return success_response(tokens, "Token refreshed successfully.")


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Authentication"],
        request=RefreshSerializer,
        responses={205: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AccountService.revoke_refresh_token(serializer.validated_data["refresh"])
        return success_response(None, "Logged out successfully.", status.HTTP_205_RESET_CONTENT)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Authentication"], request=None, responses={200: UserSerializer})
    def get(self, request):
        return success_response(UserSerializer(request.user).data, "Profile retrieved successfully.")

    @extend_schema(
        tags=["Authentication"],
        request=ProfileUpdateSerializer,
        responses={200: UserSerializer},
    )
    def put(self, request):
        serializer = ProfileUpdateSerializer(instance=request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AccountService.update_profile(request.user, serializer.validated_data)
        return success_response(UserSerializer(user).data, "Profile updated successfully.")
