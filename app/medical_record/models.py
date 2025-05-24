from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from app.core.models import TimeStampedModel
from app.appointment.models import Appointment
from app.medical_record.managers import (
    MedicalRecordManager,
    LabResultManager,
    PrescriptionManager,
    ReviewManager,
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


class Prescription(TimeStampedModel):
    """Individual prescriptions within medical records"""

    objects = PrescriptionManager()

    medical_record = models.ForeignKey(
        MedicalRecord, on_delete=models.CASCADE, related_name="prescriptions"
    )

    medication_name = models.CharField(max_length=200, db_index=True)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    instructions = models.TextField(blank=True)

    # Additional prescription details
    quantity = models.PositiveIntegerField(
        null=True, blank=True, help_text="Number of pills/units"
    )
    refills = models.PositiveIntegerField(
        default=0, help_text="Number of refills allowed"
    )
    is_generic_allowed = models.BooleanField(default=True)

    # Status tracking
    is_active = models.BooleanField(default=True, db_index=True)
    date_prescribed = models.DateField(auto_now_add=True)
    date_filled = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "prescriptions"
        indexes = [
            models.Index(fields=["medication_name"]),
            models.Index(fields=["medical_record"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.medication_name} - {self.dosage}"

    @property
    def patient(self):
        """Get the patient for this prescription."""
        return self.medical_record.patient

    @property
    def doctor(self):
        """Get the prescribing doctor."""
        return self.medical_record.doctor


class LabResult(TimeStampedModel):
    """Lab results and test results"""

    objects = LabResultManager()

    medical_record = models.ForeignKey(
        MedicalRecord, on_delete=models.CASCADE, related_name="lab_results_records"
    )

    test_name = models.CharField(max_length=200, db_index=True)
    test_type = models.CharField(
        max_length=50,
        choices=[
            ("blood", "Blood Test"),
            ("urine", "Urine Test"),
            ("imaging", "Imaging"),
            ("biopsy", "Biopsy"),
            ("culture", "Culture"),
            ("other", "Other"),
        ],
        default="blood",
    )

    result_value = models.CharField(max_length=100, blank=True)
    result_unit = models.CharField(max_length=50, blank=True)
    reference_range = models.CharField(max_length=100, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("normal", "Normal"),
            ("abnormal", "Abnormal"),
            ("critical", "Critical"),
            ("pending", "Pending"),
        ],
        default="pending",
    )

    notes = models.TextField(blank=True)
    ordered_date = models.DateField()
    result_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "lab_results"
        indexes = [
            models.Index(fields=["test_name"]),
            models.Index(fields=["status"]),
            models.Index(fields=["medical_record"]),
        ]

    def __str__(self):
        return f"{self.test_name} - {self.status}"

    @property
    def is_abnormal(self):
        """Check if result is abnormal or critical."""
        return self.status in ["abnormal", "critical"]


class Review(TimeStampedModel):
    """Patient reviews for doctors"""

    objects = ReviewManager()

    patient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="given_reviews"
    )
    doctor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_reviews"
    )
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="review",
        null=True,
        blank=True,
    )

    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars",
    )
    review_text = models.TextField(blank=True)

    # Review categories
    communication_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True
    )
    professionalism_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True
    )
    wait_time_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True
    )

    is_verified = models.BooleanField(default=False)
    is_anonymous = models.BooleanField(default=False)

    class Meta:
        db_table = "reviews"
        unique_together = ["patient", "doctor", "appointment"]
        indexes = [
            models.Index(fields=["doctor", "rating"]),
            models.Index(fields=["is_verified"]),
        ]

    def __str__(self):
        patient_name = (
            "Anonymous" if self.is_anonymous else self.patient.get_full_name()
        )
        return f"Review by {patient_name} for Dr. {self.doctor.get_full_name()} - {self.rating} stars"
