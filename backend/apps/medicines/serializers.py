from rest_framework import serializers

from .models import MedicationLog, Medicine, MedicineReminder


class MedicineSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Medicine
        fields = (
            "id",
            "user",
            "name",
            "dosage",
            "instructions",
            "start_date",
            "end_date",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "created_at", "updated_at")

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date cannot be before start date."})
        return attrs


class MedicineReminderSerializer(serializers.ModelSerializer):
    days_of_week = serializers.ListField(
        child=serializers.ChoiceField(choices=MedicineReminder.Weekday.choices),
        required=False,
        default=list,
    )

    class Meta:
        model = MedicineReminder
        fields = ("id", "medicine", "reminder_time", "days_of_week", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "medicine", "created_at", "updated_at")

    def validate_days_of_week(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Each weekday can appear only once.")
        return value


class MedicationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationLog
        fields = ("id", "medicine", "status", "taken_at", "note", "created_at")
        read_only_fields = fields


class MarkTakenSerializer(serializers.Serializer):
    note = serializers.CharField(max_length=300, required=False, allow_blank=True)
