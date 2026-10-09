from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from common.utils.responses import success_response

from .models import MedicationLog, Medicine, MedicineReminder
from .permissions import IsPatient
from .serializers import (
    MarkTakenSerializer,
    MedicationLogSerializer,
    MedicineReminderSerializer,
    MedicineSerializer,
)
from .services import MedicineService


class MedicineCollectionView(APIView):
    permission_classes = [IsPatient]

    @extend_schema(tags=["Medicines"], request=MedicineSerializer, responses={201: MedicineSerializer})
    def post(self, request):
        serializer = MedicineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        medicine = MedicineService.create_medicine(request.user, serializer.validated_data)
        return success_response(
            MedicineSerializer(medicine).data,
            "Medicine added successfully.",
            status.HTTP_201_CREATED,
        )

    @extend_schema(tags=["Medicines"], request=None, responses={200: MedicineSerializer(many=True)})
    def get(self, request):
        medicines = Medicine.objects.filter(user=request.user).prefetch_related("reminders")
        return success_response(MedicineSerializer(medicines, many=True).data, "Medicines retrieved successfully.")


class MedicineDetailView(APIView):
    permission_classes = [IsPatient]

    def get_medicine(self, request, pk):
        return get_object_or_404(Medicine, pk=pk, user=request.user)

    @extend_schema(tags=["Medicines"], request=None, responses={200: MedicineSerializer})
    def get(self, request, pk):
        medicine = self.get_medicine(request, pk)
        return success_response(MedicineSerializer(medicine).data, "Medicine retrieved successfully.")

    @extend_schema(tags=["Medicines"], request=MedicineSerializer, responses={200: MedicineSerializer})
    def put(self, request, pk):
        medicine = self.get_medicine(request, pk)
        serializer = MedicineSerializer(medicine, data=request.data)
        serializer.is_valid(raise_exception=True)
        medicine = MedicineService.update_medicine(medicine, serializer.validated_data)
        return success_response(MedicineSerializer(medicine).data, "Medicine updated successfully.")

    @extend_schema(tags=["Medicines"], request=MedicineSerializer, responses={200: MedicineSerializer})
    def patch(self, request, pk):
        medicine = self.get_medicine(request, pk)
        serializer = MedicineSerializer(medicine, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        medicine = MedicineService.update_medicine(medicine, serializer.validated_data)
        return success_response(MedicineSerializer(medicine).data, "Medicine updated successfully.")

    @extend_schema(tags=["Medicines"], request=None, responses={200: OpenApiTypes.OBJECT})
    def delete(self, request, pk):
        medicine = self.get_medicine(request, pk)
        MedicineService.delete_medicine(medicine)
        return success_response(None, "Medicine deleted successfully.")


class ReminderCollectionView(APIView):
    permission_classes = [IsPatient]

    def get_medicine(self, request, pk):
        return get_object_or_404(Medicine, pk=pk, user=request.user)

    @extend_schema(
        tags=["Medicines"],
        request=MedicineReminderSerializer,
        responses={201: MedicineReminderSerializer},
    )
    def post(self, request, pk):
        medicine = self.get_medicine(request, pk)
        serializer = MedicineReminderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reminder = MedicineService.create_reminder(medicine, serializer.validated_data)
        return success_response(
            MedicineReminderSerializer(reminder).data,
            "Reminder created successfully.",
            status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=["Medicines"], request=None, responses={200: MedicineReminderSerializer(many=True)}
    )
    def get(self, request, pk):
        medicine = self.get_medicine(request, pk)
        reminders = medicine.reminders.all()
        return success_response(
            MedicineReminderSerializer(reminders, many=True).data,
            "Reminders retrieved successfully.",
        )


class ReminderDetailView(APIView):
    permission_classes = [IsPatient]

    def get_reminder(self, request, pk, reminder_id):
        return get_object_or_404(
            MedicineReminder,
            pk=reminder_id,
            medicine_id=pk,
            medicine__user=request.user,
        )

    @extend_schema(
        tags=["Medicines"],
        request=MedicineReminderSerializer,
        responses={200: MedicineReminderSerializer},
    )
    def put(self, request, pk, reminder_id):
        reminder = self.get_reminder(request, pk, reminder_id)
        serializer = MedicineReminderSerializer(reminder, data=request.data)
        serializer.is_valid(raise_exception=True)
        reminder = MedicineService.update_reminder(reminder, serializer.validated_data)
        return success_response(MedicineReminderSerializer(reminder).data, "Reminder updated successfully.")

    @extend_schema(
        tags=["Medicines"], request=MedicineReminderSerializer, responses={200: MedicineReminderSerializer}
    )
    def patch(self, request, pk, reminder_id):
        reminder = self.get_reminder(request, pk, reminder_id)
        serializer = MedicineReminderSerializer(reminder, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        reminder = MedicineService.update_reminder(reminder, serializer.validated_data)
        return success_response(MedicineReminderSerializer(reminder).data, "Reminder updated successfully.")

    @extend_schema(tags=["Medicines"], request=None, responses={200: OpenApiTypes.OBJECT})
    def delete(self, request, pk, reminder_id):
        reminder = self.get_reminder(request, pk, reminder_id)
        MedicineService.delete_reminder(reminder)
        return success_response(None, "Reminder deleted successfully.")


class MarkMedicineTakenView(APIView):
    permission_classes = [IsPatient]

    @extend_schema(
        tags=["Medicines"],
        request=MarkTakenSerializer,
        responses={201: MedicationLogSerializer},
    )
    def post(self, request, pk):
        medicine = get_object_or_404(Medicine, pk=pk, user=request.user)
        serializer = MarkTakenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        log = MedicineService.mark_taken(medicine, serializer.validated_data.get("note", ""))
        return success_response(
            MedicationLogSerializer(log).data,
            "Medicine marked as taken.",
            status.HTTP_201_CREATED,
        )


class MedicationLogListView(APIView):
    permission_classes = [IsPatient]

    @extend_schema(tags=["Medicines"], request=None, responses={200: MedicationLogSerializer(many=True)})
    def get(self, request, pk):
        medicine = get_object_or_404(Medicine, pk=pk, user=request.user)
        logs = MedicationLog.objects.filter(medicine=medicine)
        return success_response(MedicationLogSerializer(logs, many=True).data, "Medication history retrieved successfully.")
