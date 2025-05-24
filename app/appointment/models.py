from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from app.core.models import TimeStampedModel
from app.appointment.managers import AppointmentManager, DoctorAvailabilityManager
import uuid


class DoctorAvailability(TimeStampedModel):
    """Doctor's weekly availability schedule"""

    objects = DoctorAvailabilityManager()

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
        "account.DoctorProfile", on_delete=models.CASCADE, related_name="availability"
    )
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "doctor_availability"
        unique_together = ["doctor", "day_of_week", "start_time"]
        indexes = [
            models.Index(fields=["doctor", "day_of_week"]),
            models.Index(fields=["doctor", "is_available"]),
        ]

    def __str__(self):
        return f"{self.doctor} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

    def clean(self):
        """Validate availability data."""
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time")

    def get_time_slots(self, slot_duration=30):
        """Generate time slots for this availability."""
        slots = []
        current_time = self.start_time

        while current_time < self.end_time:
            slots.append(current_time)
            # Add slot_duration minutes
            current_datetime = datetime.combine(datetime.today(), current_time)
            current_datetime += timedelta(minutes=slot_duration)
            current_time = current_datetime.time()

        return slots


class Appointment(TimeStampedModel):
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

    objects = AppointmentManager()

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
    appointment_date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    appointment_type = models.CharField(
        max_length=20, choices=APPOINTMENT_TYPES, default="consultation", db_index=True
    )

    # Status and Notes
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default="pending", db_index=True
    )
    patient_notes = models.TextField(
        blank=True, help_text="Patient's notes or symptoms"
    )
    doctor_notes = models.TextField(
        blank=True, help_text="Doctor's notes after appointment"
    )

    # Metadata
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
            models.Index(fields=["appointment_date", "status"]),
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

    @property
    def is_upcoming(self):
        """Check if appointment is upcoming."""
        return self.datetime > timezone.now()

    @property
    def can_be_cancelled(self):
        """Check if appointment can be cancelled."""
        return self.status in [
            "pending",
            "confirmed",
        ] and self.datetime > timezone.now() + timedelta(hours=2)

    def clean(self):
        """Validate appointment data"""
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

    def cancel(self, cancelled_by=None, reason=""):
        """Cancel the appointment."""
        if not self.can_be_cancelled:
            raise ValidationError("This appointment cannot be cancelled")

        self.status = "cancelled"
        if reason:
            self.doctor_notes = f"Cancelled: {reason}"
        self.save()

        # Send notification
        from app.notification.services import NotificationService

        notification_service = NotificationService()
        notification_service.send_appointment_cancelled_notification(self, cancelled_by)

    def confirm(self):
        """Confirm the appointment."""
        if self.status != "pending":
            raise ValidationError("Only pending appointments can be confirmed")

        self.status = "confirmed"
        self.save()

        # Send confirmation notification
        from app.notification.services import NotificationService

        notification_service = NotificationService()
        notification_service.send_appointment_confirmed_notification(self)

    def complete(self):
        """Mark appointment as completed."""
        if self.status not in ["confirmed", "in_progress"]:
            raise ValidationError(
                "Only confirmed or in-progress appointments can be completed"
            )

        self.status = "completed"
        self.save()
