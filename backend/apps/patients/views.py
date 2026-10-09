from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from common.utils.responses import success_response

from .models import PatientProfile
from .permissions import IsPatientOrAdmin
from .serializers import PatientProfileSerializer
from .services import PatientProfileService


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
