from django.contrib import admin

from .models import PatientProfile


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "date_of_birth", "gender", "blood_group", "updated_at")
    search_fields = ("user__email", "user__name")
    readonly_fields = ("created_at", "updated_at")
