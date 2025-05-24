from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from app.core.models import TimeStampedModel
from app.core.validators import validate_phone_number, validate_medical_license
from app.account.managers import UserProfileManager, DoctorProfileManager


class UserProfile(TimeStampedModel):
    """Extended user profile with healthcare-specific fields"""

    objects = UserProfileManager()

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
    role = models.CharField(
        max_length=10, choices=ROLE_CHOICES, default="patient", db_index=True
    )

    # Contact Information
    phone = models.CharField(
        max_length=17,
        blank=True,
        validators=[validate_phone_number],
        help_text="Phone number in international format",
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(
        max_length=17, blank=True, validators=[validate_phone_number]
    )

    # Healthcare Information
    medical_history = models.TextField(
        blank=True, help_text="Patient's medical history, allergies, etc."
    )
    insurance_info = models.TextField(blank=True)

    # Profile Settings
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    timezone = models.CharField(max_length=50, default="UTC")

    class Meta:
        db_table = "user_profiles"
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["user", "role"]),
        ]

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

    def get_dashboard_data(self):
        """Get role-specific dashboard data."""
        if self.role == "patient":
            return self._get_patient_dashboard_data()
        elif self.role == "doctor":
            return self._get_doctor_dashboard_data()
        return {}

    def _get_patient_dashboard_data(self):
        """Get dashboard data for patients."""
        from app.appointment.models import Appointment

        upcoming_appointments = Appointment.objects.filter(
            patient=self.user,
            appointment_date__gte=timezone.now().date(),
            status__in=["pending", "confirmed"],
        ).count()

        total_appointments = Appointment.objects.filter(patient=self.user).count()
        completed_visits = Appointment.objects.filter(
            patient=self.user, status="completed"
        ).count()

        return {
            "upcoming_appointments": upcoming_appointments,
            "total_appointments": total_appointments,
            "completed_visits": completed_visits,
        }

    def _get_doctor_dashboard_data(self):
        """Get dashboard data for doctors."""
        from app.appointment.models import Appointment
        from app.medical_record.models import MedicalRecord

        today = timezone.now().date()

        todays_appointments = Appointment.objects.filter(
            doctor=self.user,
            appointment_date=today,
            status__in=["pending", "confirmed", "in_progress"],
        ).count()

        total_patients = (
            User.objects.filter(patient_appointments__doctor=self.user)
            .distinct()
            .count()
        )

        pending_reviews = MedicalRecord.objects.filter(
            appointment__doctor=self.user, diagnosis=""
        ).count()

        return {
            "todays_appointments": todays_appointments,
            "total_patients": total_patients,
            "pending_reviews": pending_reviews,
        }


class DoctorProfile(TimeStampedModel):
    """Additional information specific to doctors"""

    objects = DoctorProfileManager()

    user_profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, limit_choices_to={"role": "doctor"}
    )

    # Professional Information
    license_number = models.CharField(
        max_length=50,
        unique=True,
        validators=[validate_medical_license],
        help_text="Medical license number in format: ABC-123456",
    )
    specialty = models.CharField(max_length=100, db_index=True)
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
    is_available = models.BooleanField(default=True, db_index=True)
    accepts_new_patients = models.BooleanField(default=True)

    class Meta:
        db_table = "doctor_profiles"
        indexes = [
            models.Index(fields=["specialty"]),
            models.Index(fields=["is_available"]),
            models.Index(fields=["specialty", "is_available"]),
        ]

    def __str__(self):
        return f"Dr. {self.user_profile.full_name} - {self.specialty}"

    def update_rating(self):
        """Update doctor's rating based on reviews."""
        from app.medical_record.models import Review

        reviews = Review.objects.filter(doctor=self.user_profile.user)
        if reviews.exists():
            avg_rating = reviews.aggregate(avg_rating=models.Avg("rating"))[
                "avg_rating"
            ]
            self.rating = round(avg_rating, 2)
            self.total_reviews = reviews.count()
            self.save(update_fields=["rating", "total_reviews"])

    def get_available_slots(self, date):
        """Get available time slots for a specific date."""
        from app.appointment.services import AppointmentService

        service = AppointmentService()
        return service.get_available_slots(self.user_profile.user, date)
