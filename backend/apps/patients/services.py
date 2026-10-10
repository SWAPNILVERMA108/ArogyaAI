from django.db import IntegrityError, transaction

from common.exceptions.api import Conflict

from .models import PatientProfile


class PatientProfileService:
    @staticmethod
    def create_profile(user, validated_data):
        try:
            with transaction.atomic():
                return PatientProfile.objects.create(user=user, **validated_data)
        except IntegrityError as exc:
            raise Conflict("A patient profile already exists for this account.") from exc

    @staticmethod
    def update_profile(profile, validated_data):
        for field, value in validated_data.items():
            setattr(profile, field, value)
        profile.save(update_fields=[*validated_data.keys(), "updated_at"])
        return profile


class PatientAccessService:
    @staticmethod
    def grant(patient, doctor_email):
        from django.contrib.auth import get_user_model
        from rest_framework.exceptions import NotFound

        from .models import PatientAccessGrant

        User = get_user_model()
        doctor = User.objects.filter(
            email=doctor_email.casefold(), role=User.Role.DOCTOR, is_active=True
        ).first()
        if doctor is None:
            raise NotFound("No active doctor account was found with that email.")
        grant, created = PatientAccessGrant.objects.get_or_create(patient=patient, doctor=doctor)
        if not created:
            raise Conflict("This doctor already has access.")
        return grant
