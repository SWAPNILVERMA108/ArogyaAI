from datetime import date

from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from .models import PatientProfile


class PatientProfileSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = (
            "id",
            "user",
            "date_of_birth",
            "age",
            "gender",
            "blood_group",
            "height_cm",
            "weight_kg",
            "allergies",
            "medical_history",
            "emergency_contact",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "age", "created_at", "updated_at")

    @extend_schema_field(OpenApiTypes.INT)
    def get_age(self, profile):
        if profile.date_of_birth is None:
            return None
        today = date.today()
        return today.year - profile.date_of_birth.year - (
            (today.month, today.day) < (profile.date_of_birth.month, profile.date_of_birth.day)
        )

    def validate_date_of_birth(self, value):
        if value and value > date.today():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value
