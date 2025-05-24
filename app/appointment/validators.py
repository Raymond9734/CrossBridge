from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


def validate_appointment_date(date):
    """Validate appointment date is not in the past and not too far in future."""
    if date < timezone.now().date():
        raise ValidationError("Cannot schedule appointments in the past")
    
    # Don't allow booking more than 3 months in advance
    max_advance_date = timezone.now().date() + timedelta(days=90)
    if date > max_advance_date:
        raise ValidationError("Cannot schedule appointments more than 3 months in advance")


def validate_appointment_time_slot(doctor, date, start_time, end_time, exclude_appointment=None):
    """Validate that the appointment time slot is available."""
    from .models import Appointment
    
    conflicts = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=date,
        status__in=["pending", "confirmed", "in_progress"]
    )
    
    if exclude_appointment:
        conflicts = conflicts.exclude(id=exclude_appointment.id)
    
    for appointment in conflicts:
        if start_time < appointment.end_time and end_time > appointment.start_time:
            raise ValidationError(f"Conflicts with existing appointment at {appointment.start_time}")