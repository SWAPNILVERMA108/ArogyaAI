import math

from rest_framework import serializers


class NearbyFacilitiesQuerySerializer(serializers.Serializer):
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)
    city = serializers.CharField(required=False, max_length=100, trim_whitespace=True)
    pincode = serializers.CharField(required=False, max_length=16, trim_whitespace=True)
    radius = serializers.IntegerField(required=False, default=5000, min_value=100, max_value=25000)
    category = serializers.ChoiceField(
        required=False,
        choices=("hospital", "clinic", "pharmacy", "emergency"),
    )

    def validate(self, attrs):
        has_latitude = "latitude" in attrs
        has_longitude = "longitude" in attrs
        has_city_or_pin = bool(attrs.get("city") or attrs.get("pincode"))

        if has_latitude != has_longitude:
            raise serializers.ValidationError("Provide both latitude and longitude.")
        if has_latitude and has_city_or_pin:
            raise serializers.ValidationError("Use coordinates or city/postcode, not both.")
        if not has_latitude and not has_city_or_pin:
            raise serializers.ValidationError(
                "Provide latitude and longitude, or a city and/or postcode."
            )
        if has_latitude:
            latitude, longitude = attrs["latitude"], attrs["longitude"]
            if not math.isfinite(latitude) or not -90 <= latitude <= 90:
                raise serializers.ValidationError({"latitude": "Enter a valid latitude."})
            if not math.isfinite(longitude) or not -180 <= longitude <= 180:
                raise serializers.ValidationError({"longitude": "Enter a valid longitude."})
        if attrs.get("pincode") and not any(char.isalnum() for char in attrs["pincode"]):
            raise serializers.ValidationError({"pincode": "Enter a valid postcode."})
        return attrs


class FacilitySerializer(serializers.Serializer):
    name = serializers.CharField()
    address = serializers.CharField(allow_blank=True)
    phone = serializers.CharField(allow_null=True, allow_blank=True)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    distance_km = serializers.FloatField(allow_null=True)
    facility_type = serializers.CharField()


class NearbyFacilitiesResponseSerializer(serializers.Serializer):
    facilities = FacilitySerializer(many=True)
    attribution = serializers.CharField()
    attribution_url = serializers.URLField()
