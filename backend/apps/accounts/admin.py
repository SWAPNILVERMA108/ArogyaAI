from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class ArogyaUserAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "name", "role", "is_active", "is_staff")
    search_fields = ("email", "name", "phone")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal information", {"fields": ("name", "phone", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")} ),
    )
    readonly_fields = ("created_at", "updated_at")
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "name", "phone", "role", "password1", "password2")}),
    )
