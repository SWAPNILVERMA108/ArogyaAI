from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q


class EmergencyContact(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emergency_contacts",
    )
    name = models.CharField(max_length=150)
    phone = models.CharField(
        max_length=24,
        validators=[RegexValidator(r"^[0-9+() -]+$", "Enter a valid phone number.")],
    )
    relationship = models.CharField(max_length=80, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_primary", "name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=("user",),
                condition=Q(is_primary=True),
                name="emergency_primary_user_uniq",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.user.email})"
