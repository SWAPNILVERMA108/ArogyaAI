from django.conf import settings
from django.db import models
from django.utils import timezone


class Medicine(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="medicines",
    )
    name = models.CharField(max_length=160)
    dosage = models.CharField(max_length=100, blank=True)
    instructions = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "-created_at"]

    def __str__(self):
        return f"{self.name} ({self.user.email})"


class MedicineReminder(models.Model):
    class Weekday(models.TextChoices):
        MONDAY = "MON", "Monday"
        TUESDAY = "TUE", "Tuesday"
        WEDNESDAY = "WED", "Wednesday"
        THURSDAY = "THU", "Thursday"
        FRIDAY = "FRI", "Friday"
        SATURDAY = "SAT", "Saturday"
        SUNDAY = "SUN", "Sunday"

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name="reminders",
    )
    reminder_time = models.TimeField()
    days_of_week = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["reminder_time"]
        constraints = [
            models.UniqueConstraint(
                fields=("medicine", "reminder_time"),
                name="unique_medicine_reminder_time",
            ),
        ]

    def __str__(self):
        return f"{self.medicine.name} at {self.reminder_time}"


class MedicationLog(models.Model):
    class Status(models.TextChoices):
        TAKEN = "TAKEN", "Taken"

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name="logs",
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.TAKEN)
    taken_at = models.DateTimeField(default=timezone.now)
    note = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-taken_at"]

    def __str__(self):
        return f"{self.medicine.name}: {self.get_status_display()} at {self.taken_at}"
