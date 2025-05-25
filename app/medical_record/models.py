from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from app.core.models import TimeStampedModel
from app.appointment.models import Appointment
from app.medical_record.managers import (
    MedicalRecordManager,
)


class MedicalRecord(TimeStampedModel):
    """Medical records tied to appointments"""

    objects = MedicalRecordManager()

    appointment = models.OneToOneField(
        Appointment, on_delete=models.CASCADE, related_name="medical_record"
    )

    # Medical Information
    diagnosis = models.TextField(blank=True)
    treatment = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
    lab_results = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False, db_index=True)
    follow_up_date = models.DateField(null=True, blank=True)

    # Vitals
    blood_pressure_systolic = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(70), MaxValueValidator(250)],
        help_text="Systolic blood pressure (70-250 mmHg)",
    )
    blood_pressure_diastolic = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(150)],
        help_text="Diastolic blood pressure (40-150 mmHg)",
    )
    heart_rate = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(220)],
        help_text="Heart rate (30-220 bpm)",
    )
    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(95.0), MaxValueValidator(110.0)],
        help_text="Body temperature (95.0-110.0°F)",
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(10.0), MaxValueValidator(1000.0)],
        help_text="Weight in pounds (10-1000 lbs)",
    )
    height = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(12.0), MaxValueValidator(96.0)],
        help_text="Height in inches (12-96 inches)",
    )

    # Additional fields
    allergies = models.TextField(blank=True, help_text="Known allergies")
    medications = models.TextField(blank=True, help_text="Current medications")
    medical_history = models.TextField(blank=True, help_text="Relevant medical history")

    # Privacy and access
    is_sensitive = models.BooleanField(
        default=False, help_text="Mark as sensitive/confidential record"
    )

    class Meta:
        db_table = "medical_records"
        indexes = [
            models.Index(fields=["appointment"]),
            models.Index(fields=["follow_up_required"]),
            # models.Index(fields=["appointment__patient"]),
            # models.Index(fields=["appointment__doctor"]),
        ]

    def __str__(self):
        return f"Medical Record for {self.appointment}"

    @property
    def patient(self):
        """Get the patient for this medical record."""
        return self.appointment.patient

    @property
    def doctor(self):
        """Get the doctor for this medical record."""
        return self.appointment.doctor

    @property
    def bmi(self):
        """Calculate BMI if height and weight are available."""
        if self.height and self.weight:
            # Convert to metric: weight in kg, height in meters
            weight_kg = float(self.weight) * 0.453592  # pounds to kg
            height_m = float(self.height) * 0.0254  # inches to meters
            return round(weight_kg / (height_m**2), 1)
        return None

    @property
    def blood_pressure(self):
        """Get formatted blood pressure string."""
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None

    def get_vitals_summary(self):
        """Get a summary of all vital signs."""
        vitals = {}

        if self.blood_pressure:
            vitals["Blood Pressure"] = f"{self.blood_pressure} mmHg"

        if self.heart_rate:
            vitals["Heart Rate"] = f"{self.heart_rate} bpm"

        if self.temperature:
            vitals["Temperature"] = f"{self.temperature}°F"

        if self.weight:
            vitals["Weight"] = f"{self.weight} lbs"

        if self.height:
            vitals["Height"] = f"{self.height} inches"

        if self.bmi:
            vitals["BMI"] = str(self.bmi)

        return vitals
