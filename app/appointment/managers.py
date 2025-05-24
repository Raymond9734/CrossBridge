from django.db import models
from django.utils import timezone
from app.core.managers import CacheableManager


class AppointmentManager(CacheableManager):
    """Custom manager for Appointment model."""

    def upcoming(self):
        """Get upcoming appointments."""
        return self.filter(
            appointment_date__gte=timezone.now().date(),
            status__in=["pending", "confirmed"],
        )

    def today(self):
        """Get today's appointments."""
        return self.filter(appointment_date=timezone.now().date())

    def for_patient(self, patient, status=None):
        """Get appointments for a specific patient."""
        queryset = self.filter(patient=patient)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def for_doctor(self, doctor, date=None):
        """Get appointments for a specific doctor."""
        queryset = self.filter(doctor=doctor)
        if date:
            queryset = queryset.filter(appointment_date=date)
        return queryset

    def in_date_range(self, start_date, end_date):
        """Get appointments in date range."""
        return self.filter(
            appointment_date__gte=start_date, appointment_date__lte=end_date
        )

    def conflicting_appointments(
        self, doctor, date, start_time, end_time, exclude_id=None
    ):
        """Find conflicting appointments."""
        queryset = self.filter(
            doctor=doctor,
            appointment_date=date,
            status__in=["pending", "confirmed", "in_progress"],
        )

        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)

        conflicts = []
        for apt in queryset:
            if start_time < apt.end_time and end_time > apt.start_time:
                conflicts.append(apt)

        return conflicts


class DoctorAvailabilityManager(models.Manager):
    """Custom manager for DoctorAvailability model."""

    def for_doctor(self, doctor):
        """Get availability for a specific doctor."""
        return self.filter(doctor=doctor)

    def available_only(self):
        """Get only available slots."""
        return self.filter(is_available=True)

    def for_day(self, day_of_week):
        """Get availability for a specific day."""
        return self.filter(day_of_week=day_of_week)
