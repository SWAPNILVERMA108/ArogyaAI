import math
import re

from rest_framework import serializers

from .models import EmergencyContact


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ("id", "name", "phone", "relationship", "is_primary", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_phone(self, value):
        digits = re.sub(r"\D", "", value)
        if not 7 <= len(digits) <= 15:
            raise serializers.ValidationError("Phone number must contain 7 to 15 digits.")
        return value.strip()


class LocationShareRequestSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    emergency_contact_id = serializers.IntegerField(required=False, min_value=1)

    def validate(self, attrs):
        latitude, longitude = attrs["latitude"], attrs["longitude"]
        if not math.isfinite(latitude) or not -90 <= latitude <= 90:
            raise serializers.ValidationError({"latitude": "Enter a valid latitude."})
        if not math.isfinite(longitude) or not -180 <= longitude <= 180:
            raise serializers.ValidationError({"longitude": "Enter a valid longitude."})
        return attrs


class EmergencyInfoSerializer(serializers.Serializer):
    emergency_number = serializers.CharField(allow_blank=True)
    emergency_label = serializers.CharField()
    call_uri = serializers.CharField(allow_blank=True)
    information_url = serializers.URLField(allow_blank=True)
    disclaimer = serializers.CharField()
    guidance = serializers.ListField(child=serializers.CharField())
    nearby_facilities_endpoint = serializers.CharField()


class LocationShareResponseSerializer(serializers.Serializer):
    share_url = serializers.URLField()
    message = serializers.CharField()
    contact = EmergencyContactSerializer(allow_null=True)
    notice = serializers.CharField()
