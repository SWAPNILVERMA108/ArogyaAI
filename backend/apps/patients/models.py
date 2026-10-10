from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class PatientProfile(models.Model):
    class Gender(models.TextChoices):
        FEMALE = "FEMALE", "Female"
        MALE = "MALE", "Male"
        OTHER = "OTHER", "Other"
        PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", "Prefer not to say"

    class BloodGroup(models.TextChoices):
        A_POSITIVE = "A+", "A+"
        A_NEGATIVE = "A-", "A-"
        B_POSITIVE = "B+", "B+"
        B_NEGATIVE = "B-", "B-"
        AB_POSITIVE = "AB+", "AB+"
        AB_NEGATIVE = "AB-", "AB-"
        O_POSITIVE = "O+", "O+"
        O_NEGATIVE = "O-", "O-"
        UNKNOWN = "UNKNOWN", "Unknown"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile",
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)
    blood_group = models.CharField(max_length=7, choices=BloodGroup.choices, blank=True)
    height_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(300)],
    )
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(700)],
    )
    allergies = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Patient profile: {self.user.email}"


class PatientAccessGrant(models.Model):
    """A patient's explicit consent for one doctor to view their health summary."""

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="access_grants",
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_grants",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=("patient", "doctor"), name="unique_patient_doctor_grant"),
        ]

    def __str__(self):
        return f"{self.patient_id} -> {self.doctor_id}"
