from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import IsDoctor
from apps.medicines.serializers import MedicineSerializer
from common.utils.responses import success_response

from .models import PatientAccessGrant, PatientProfile
from .serializers import PatientProfileSerializer


def _summary(grant):
    patient = grant.patient
    profile = PatientProfile.objects.filter(user=patient).first()
    return {
        "patient_id": patient.id,
        "name": patient.name,
        "email": patient.email,
        "phone": patient.phone,
        "granted_at": grant.created_at,
        "profile": PatientProfileSerializer(profile).data if profile else None,
    }


class DoctorPatientListView(APIView):
    """Patients who explicitly granted this doctor access."""

    permission_classes = [IsDoctor]

    @extend_schema(tags=["Doctor"], request=None, responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        grants = PatientAccessGrant.objects.filter(doctor=request.user).select_related("patient")
        return success_response([_summary(grant) for grant in grants], "Patients retrieved successfully.")


class DoctorPatientDetailView(APIView):
    permission_classes = [IsDoctor]

    @extend_schema(
        tags=["Doctor"], operation_id="doctor_patient_summary", request=None, responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request, patient_id):
        grant = get_object_or_404(
            PatientAccessGrant.objects.select_related("patient"),
            doctor=request.user,
            patient_id=patient_id,
        )
        data = _summary(grant)
        medicines = grant.patient.medicines.filter(is_active=True)
        data["medicines"] = MedicineSerializer(medicines, many=True).data
        return success_response(data, "Patient summary retrieved successfully.")
