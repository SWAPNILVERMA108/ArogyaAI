from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from common.utils.responses import success_response

from .models import PatientAccessGrant, PatientProfile
from .permissions import IsPatientOrAdmin
from .serializers import (
    AccessGrantCreateSerializer,
    AccessGrantSerializer,
    PatientProfileSerializer,
)
from .services import PatientAccessService, PatientProfileService


class PatientProfileCollectionView(APIView):
    permission_classes = [IsPatientOrAdmin]

    @extend_schema(
        tags=["Patients"],
        request=PatientProfileSerializer,
        responses={201: PatientProfileSerializer},
    )
    def post(self, request):
        serializer = PatientProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = PatientProfileService.create_profile(request.user, serializer.validated_data)
        return success_response(
            PatientProfileSerializer(profile).data,
            "Patient profile created successfully.",
            status.HTTP_201_CREATED,
        )


class MyPatientProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Patients"], request=None, responses={200: PatientProfileSerializer})
    def get(self, request):
        profile = get_object_or_404(PatientProfile, user=request.user)
        return success_response(PatientProfileSerializer(profile).data, "Patient profile retrieved successfully.")

    @extend_schema(
        tags=["Patients"],
        request=PatientProfileSerializer,
        responses={200: PatientProfileSerializer},
    )
    def put(self, request):
        profile = get_object_or_404(PatientProfile, user=request.user)
        serializer = PatientProfileSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = PatientProfileService.update_profile(profile, serializer.validated_data)
        return success_response(PatientProfileSerializer(profile).data, "Patient profile updated successfully.")


class PatientProfileDetailView(APIView):
    permission_classes = [IsPatientOrAdmin]

    @extend_schema(tags=["Patients"], request=None, responses={200: PatientProfileSerializer})
    def get(self, request, pk):
        profiles = PatientProfile.objects.select_related("user")
        if request.user.role != "ADMIN":
            profiles = profiles.filter(user=request.user)
        profile = get_object_or_404(profiles, pk=pk)
        return success_response(PatientProfileSerializer(profile).data, "Patient profile retrieved successfully.")


class AccessGrantCollectionView(APIView):
    permission_classes = [IsPatientOrAdmin]
    # Looking up doctor emails could be used to enumerate doctor accounts, so cap attempts.
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "access"

    @extend_schema(tags=["Patients"], request=None, responses={200: AccessGrantSerializer(many=True)})
    def get(self, request):
        grants = PatientAccessGrant.objects.filter(patient=request.user).select_related("doctor")
        return success_response(AccessGrantSerializer(grants, many=True).data, "Access grants retrieved successfully.")

    @extend_schema(
        tags=["Patients"],
        request=AccessGrantCreateSerializer,
        responses={201: AccessGrantSerializer},
    )
    def post(self, request):
        serializer = AccessGrantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        grant = PatientAccessService.grant(request.user, serializer.validated_data["doctor_email"])
        return success_response(
            AccessGrantSerializer(grant).data,
            "Doctor access granted.",
            status.HTTP_201_CREATED,
        )


class AccessGrantDetailView(APIView):
    permission_classes = [IsPatientOrAdmin]

    @extend_schema(tags=["Patients"], request=None, responses={200: OpenApiTypes.OBJECT})
    def delete(self, request, pk):
        grant = get_object_or_404(PatientAccessGrant, pk=pk, patient=request.user)
        grant.delete()
        return success_response(None, "Doctor access revoked.")
