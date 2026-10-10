from rest_framework import serializers

from .models import HealthCategory, HealthTip


class HealthCategorySerializer(serializers.ModelSerializer):
    tip_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = HealthCategory
        fields = ("id", "slug", "name", "name_hi", "tip_count")
        read_only_fields = fields


class HealthTipSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = HealthTip
        fields = ("id", "slug", "category", "title", "title_hi", "body", "body_hi")
        read_only_fields = fields


class HealthTipQuerySerializer(serializers.Serializer):
    category = serializers.SlugField(required=False)
