from django.contrib import admin

from .models import MedicationLog, Medicine, MedicineReminder


class MedicineReminderInline(admin.TabularInline):
    model = MedicineReminder
    extra = 0


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "dosage", "is_active", "start_date", "end_date")
    list_filter = ("is_active",)
    search_fields = ("name", "user__email", "user__name")
    inlines = (MedicineReminderInline,)


@admin.register(MedicationLog)
class MedicationLogAdmin(admin.ModelAdmin):
    list_display = ("medicine", "status", "taken_at")
    list_filter = ("status",)
    search_fields = ("medicine__name", "medicine__user__email")
    readonly_fields = ("created_at",)
