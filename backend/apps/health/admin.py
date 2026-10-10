from django.contrib import admin

from .models import HealthCategory, HealthTip

admin.site.register(HealthCategory)
admin.site.register(HealthTip)
