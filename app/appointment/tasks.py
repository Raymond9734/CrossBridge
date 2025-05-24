from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Appointment


@shared_task
def send_appointment_reminders():
    """Send appointment reminders."""
    from app.notification.services import NotificationService

    # Get appointments for tomorrow
    tomorrow = timezone.now().date() + timedelta(days=1)
    appointments = Appointment.objects.filter(
        appointment_date=tomorrow, status="confirmed"
    )

    notification_service = NotificationService()

    for appointment in appointments:
        notification_service.send_appointment_reminder(appointment)

    return f"Sent reminders for {appointments.count()} appointments"


@shared_task
def cleanup_expired_appointments():
    """Clean up old completed/cancelled appointments."""
    cutoff_date = timezone.now().date() - timedelta(days=90)

    expired_count = Appointment.objects.filter(
        appointment_date__lt=cutoff_date,
        status__in=["completed", "cancelled", "no_show"],
    ).count()

    # In a real system, you might archive these instead of deleting
    # For now, we'll just count them

    return f"Found {expired_count} expired appointments"


@shared_task
def mark_no_show_appointments():
    """Mark appointments as no-show if patient didn't arrive."""
    # Mark appointments that started more than 30 minutes ago as no-show
    cutoff_time = timezone.now() - timedelta(minutes=30)

    no_show_appointments = Appointment.objects.filter(
        status="confirmed",
        appointment_date=cutoff_time.date(),
        start_time__lte=cutoff_time.time(),
    )

    count = no_show_appointments.update(status="no_show")

    return f"Marked {count} appointments as no-show"
