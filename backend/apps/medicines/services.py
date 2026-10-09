from django.db import IntegrityError, transaction

from common.exceptions.api import Conflict

from .models import MedicationLog, Medicine, MedicineReminder


class MedicineService:
    @staticmethod
    def create_medicine(user, validated_data):
        return Medicine.objects.create(user=user, **validated_data)

    @staticmethod
    def update_medicine(medicine, validated_data):
        for field, value in validated_data.items():
            setattr(medicine, field, value)
        medicine.save(update_fields=[*validated_data.keys(), "updated_at"])
        return medicine

    @staticmethod
    def delete_medicine(medicine):
        medicine.delete()

    @staticmethod
    def create_reminder(medicine, validated_data):
        try:
            with transaction.atomic():
                return MedicineReminder.objects.create(medicine=medicine, **validated_data)
        except IntegrityError as exc:
            raise Conflict("A reminder already exists for this medicine at that time.") from exc

    @staticmethod
    def update_reminder(reminder, validated_data):
        for field, value in validated_data.items():
            setattr(reminder, field, value)
        try:
            with transaction.atomic():
                reminder.save(update_fields=[*validated_data.keys(), "updated_at"])
        except IntegrityError as exc:
            raise Conflict("A reminder already exists for this medicine at that time.") from exc
        return reminder

    @staticmethod
    def delete_reminder(reminder):
        reminder.delete()

    @staticmethod
    def mark_taken(medicine, note=""):
        if not medicine.is_active:
            raise Conflict("Inactive medicines cannot be marked as taken.")
        return MedicationLog.objects.create(
            medicine=medicine,
            status=MedicationLog.Status.TAKEN,
            note=note,
        )
