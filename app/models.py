from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import datetime

# Signal handlers to create profiles automatically
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid


class UserProfile(models.Model):
    """Extended user profile with healthcare-specific fields"""

    ROLE_CHOICES = [
        ("patient", "Patient"),
        ("doctor", "Doctor"),
        ("admin", "Admin"),
    ]

    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
        ("P", "Prefer not to say"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="patient")

    # Contact Information
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(
        validators=[phone_regex], max_length=17, blank=True
    )

    # Healthcare Information
    medical_history = models.TextField(
        blank=True, help_text="Patient's medical history, allergies, etc."
    )
    insurance_info = models.TextField(blank=True)

    # Profile Settings
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    timezone = models.CharField(max_length=50, default="UTC")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profiles"

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return (
                today.year
                - self.date_of_birth.year
                - (
                    (today.month, today.day)
                    < (self.date_of_birth.month, self.date_of_birth.day)
                )
            )
        return None


class DoctorProfile(models.Model):
    """Additional information specific to doctors"""

    user_profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, limit_choices_to={"role": "doctor"}
    )

    # Professional Information
    license_number = models.CharField(max_length=50, unique=True)
    specialty = models.CharField(max_length=100)
    subspecialty = models.CharField(max_length=100, blank=True)
    years_experience = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True)

    # Practice Information
    hospital_affiliation = models.CharField(max_length=200, blank=True)
    clinic_address = models.TextField(blank=True)
    consultation_fee = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Ratings and Reviews
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_reviews = models.PositiveIntegerField(default=0)

    # Availability Settings
    is_available = models.BooleanField(default=True)
    accepts_new_patients = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "doctor_profiles"

    def __str__(self):
        return f"Dr. {self.user_profile.full_name} - {self.specialty}"


class DoctorAvailability(models.Model):
    """Doctor's weekly availability schedule"""

    DAYS_OF_WEEK = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.CASCADE, related_name="availability"
    )
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    class Meta:
        db_table = "doctor_availability"
        unique_together = ["doctor", "day_of_week", "start_time"]

    def __str__(self):
        return f"{self.doctor} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class Appointment(models.Model):
    """Patient appointments with doctors"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("no_show", "No Show"),
    ]

    APPOINTMENT_TYPES = [
        ("consultation", "General Consultation"),
        ("follow_up", "Follow-up Visit"),
        ("checkup", "Regular Checkup"),
        ("emergency", "Emergency"),
        ("physical_therapy", "Physical Therapy"),
        ("lab_work", "Lab Work"),
        ("imaging", "Imaging"),
    ]

    # Unique identifier
    appointment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Participants
    patient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="patient_appointments"
    )
    doctor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="doctor_appointments"
    )

    # Appointment Details
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    appointment_type = models.CharField(
        max_length=20, choices=APPOINTMENT_TYPES, default="consultation"
    )

    # Status and Notes
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending")
    patient_notes = models.TextField(
        blank=True, help_text="Patient's notes or symptoms"
    )
    doctor_notes = models.TextField(
        blank=True, help_text="Doctor's notes after appointment"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_appointments"
    )

    class Meta:
        db_table = "appointments"
        ordering = ["-appointment_date", "-start_time"]
        indexes = [
            models.Index(fields=["appointment_date", "start_time"]),
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["doctor", "status"]),
        ]

    def __str__(self):
        return f"{self.patient.get_full_name()} with {self.doctor.get_full_name()} on {self.appointment_date}"

    @property
    def datetime(self):
        return timezone.make_aware(
            datetime.combine(self.appointment_date, self.start_time)
        )

    @property
    def duration_minutes(self):
        """Calculate appointment duration in minutes"""
        start = datetime.combine(self.appointment_date, self.start_time)
        end = datetime.combine(self.appointment_date, self.end_time)
        return int((end - start).total_seconds() / 60)

    def clean(self):
        """Validate appointment data"""
        from django.core.exceptions import ValidationError

        # Ensure end time is after start time
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time")

        # Ensure appointment is not in the past (except for admin users)
        if self.appointment_date < timezone.now().date():
            raise ValidationError("Cannot schedule appointments in the past")

        # Check for overlapping appointments
        overlapping = Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            status__in=["pending", "confirmed", "in_progress"],
        ).exclude(pk=self.pk)

        for apt in overlapping:
            if self.start_time < apt.end_time and self.end_time > apt.start_time:
                raise ValidationError(
                    f"Doctor has a conflicting appointment at {apt.start_time}"
                )


class MedicalRecord(models.Model):
    """Medical records tied to appointments"""

    appointment = models.OneToOneField(
        Appointment, on_delete=models.CASCADE, related_name="medical_record"
    )

    # Medical Information
    diagnosis = models.TextField(blank=True)
    treatment = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
    lab_results = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)

    # Vitals
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)
    temperature = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "medical_records"

    def __str__(self):
        return f"Medical Record for {self.appointment}"


class Prescription(models.Model):
    """Individual prescriptions within medical records"""

    medical_record = models.ForeignKey(
        MedicalRecord, on_delete=models.CASCADE, related_name="prescriptions"
    )

    medication_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    instructions = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "prescriptions"

    def __str__(self):
        return f"{self.medication_name} - {self.dosage}"


class Notification(models.Model):
    """System notifications for users"""

    NOTIFICATION_TYPES = [
        ("appointment_confirmed", "Appointment Confirmed"),
        ("appointment_reminder", "Appointment Reminder"),
        ("appointment_cancelled", "Appointment Cancelled"),
        ("medical_record_updated", "Medical Record Updated"),
        ("system_message", "System Message"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    # Optional related objects
    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} for {self.user.get_full_name()}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, "userprofile"):
        instance.userprofile.save()


@receiver(post_save, sender=UserProfile)
def create_doctor_profile(sender, instance, created, **kwargs):
    """Create DoctorProfile when UserProfile with role 'doctor' is created"""
    if instance.role == "doctor" and not hasattr(instance, "doctorprofile"):
        DoctorProfile.objects.create(
            user_profile=instance,
            license_number=f"LIC-{instance.user.id:06d}",  # Temporary license number
            specialty="General Medicine",  # Default specialty
        )
