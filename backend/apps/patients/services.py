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
