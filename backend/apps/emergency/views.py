from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from common.utils.responses import success_response

from .models import EmergencyContact
from .permissions import IsPatient
from .serializers import (
    EmergencyContactSerializer,
    EmergencyInfoSerializer,
    LocationShareRequestSerializer,
    LocationShareResponseSerializer,
)
from .services import EmergencyService


class EmergencyInfoView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Emergency"], request=None, responses={200: EmergencyInfoSerializer})
    def get(self, request):
        return success_response(
            EmergencyService.information(),
            "Emergency call information and general guidance retrieved.",
        )


class EmergencyContactCollectionView(APIView):
    permission_classes = [IsPatient]

    @extend_schema(
        tags=["Emergency"],
        request=EmergencyContactSerializer,
        responses={201: EmergencyContactSerializer},
    )
    def post(self, request):
        serializer = EmergencyContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = EmergencyService.create_contact(request.user, serializer.validated_data)
        return success_response(
            EmergencyContactSerializer(contact).data,
            "Emergency contact saved successfully.",
            status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=["Emergency"],
        request=None,
        responses={200: EmergencyContactSerializer(many=True)},
    )
    def get(self, request):
        contacts = EmergencyContact.objects.filter(user=request.user)
        return success_response(
            EmergencyContactSerializer(contacts, many=True).data,
            "Emergency contacts retrieved successfully.",
        )


class EmergencyContactDetailView(APIView):
    permission_classes = [IsPatient]

    def get_contact(self, request, pk):
        return get_object_or_404(EmergencyContact, pk=pk, user=request.user)

    @extend_schema(tags=["Emergency"], request=None, responses={200: EmergencyContactSerializer})
    def get(self, request, pk):
        return success_response(
            EmergencyContactSerializer(self.get_contact(request, pk)).data,
            "Emergency contact retrieved successfully.",
        )

    @extend_schema(
        tags=["Emergency"],
        request=EmergencyContactSerializer,
        responses={200: EmergencyContactSerializer},
    )
    def put(self, request, pk):
        contact = self.get_contact(request, pk)
        serializer = EmergencyContactSerializer(contact, data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = EmergencyService.update_contact(contact, serializer.validated_data)
        return success_response(EmergencyContactSerializer(contact).data, "Emergency contact updated.")

    @extend_schema(
        tags=["Emergency"],
        request=EmergencyContactSerializer,
        responses={200: EmergencyContactSerializer},
    )
    def patch(self, request, pk):
        contact = self.get_contact(request, pk)
        serializer = EmergencyContactSerializer(contact, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        contact = EmergencyService.update_contact(contact, serializer.validated_data)
        return success_response(EmergencyContactSerializer(contact).data, "Emergency contact updated.")

    @extend_schema(tags=["Emergency"], request=None, responses={200: OpenApiTypes.OBJECT})
    def delete(self, request, pk):
        EmergencyService.delete_contact(self.get_contact(request, pk))
        return success_response(None, "Emergency contact deleted.")


class LocationShareView(APIView):
    permission_classes = [IsPatient]

    @extend_schema(
        tags=["Emergency"],
        request=LocationShareRequestSerializer,
        responses={200: LocationShareResponseSerializer},
    )
    def post(self, request):
        serializer = LocationShareRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = None
        contact_id = serializer.validated_data.get("emergency_contact_id")
        if contact_id is not None:
            contact = get_object_or_404(EmergencyContact, pk=contact_id, user=request.user)
        result = EmergencyService.create_location_share(
            serializer.validated_data["latitude"],
            serializer.validated_data["longitude"],
            contact,
        )
        return success_response(
            result,
            "Location message prepared. Review before sharing; no message was sent.",
        )
