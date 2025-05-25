from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from app.core.services import BaseService
from .models import Notification, NotificationPreference
from datetime import timedelta


class NotificationService(BaseService):
    """Service for notification operations."""

    def get_model(self):
        return Notification

    def create_notification(
        self,
        user,
        notification_type,
        title,
        message,
        appointment=None,
        priority="normal",
        scheduled_for=None,
        delivery_channels=None,
        metadata=None,
    ):
        """Create a notification."""
        # Get user preferences
        preferences = self.get_user_preferences(user)

        # Set delivery channels based on preferences if not specified
        if delivery_channels is None:
            delivery_channels = []
            if preferences.should_send_notification(notification_type, "email"):
                delivery_channels.append("email")
            if preferences.should_send_notification(notification_type, "sms"):
                delivery_channels.append("sms")
            if preferences.should_send_notification(notification_type, "push"):
                delivery_channels.append("push")

        notification = self.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            appointment=appointment,
            priority=priority,
            scheduled_for=scheduled_for or timezone.now(),
            send_email="email" in delivery_channels,
            send_sms="sms" in delivery_channels,
            send_push="push" in delivery_channels,
            metadata=metadata or {},
        )

        # Clear user's notification cache
        cache.delete(f"user_notifications:{user.id}")

        return notification

    def send_appointment_request_notification(self, appointment):
        """Send notification when appointment is requested."""
        try:
            # Notify doctor about new appointment request
            self.create_notification(
                user=appointment.doctor,
                notification_type="appointment_request",
                title="New Appointment Request",
                message=f"New appointment request from {appointment.patient.get_full_name()} "
                f"on {appointment.appointment_date.strftime('%B %d, %Y')} "
                f"at {appointment.start_time.strftime('%I:%M %p')} "
                f"for {appointment.get_appointment_type_display()}.",
                appointment=appointment,
                priority="normal",
            )
        except Exception as e:
            # Log error but don't propagate to prevent booking failure
            self.logger.error(f"Failed to send appointment request notification: {e}")

    def send_appointment_confirmed_notification(self, appointment):
        """Send notification when appointment is confirmed."""
        try:
            # Notify patient that appointment is confirmed
            self.create_notification(
                user=appointment.patient,
                notification_type="appointment_confirmed",
                title="Appointment Confirmed",
                message=f"Your appointment with Dr. {appointment.doctor.get_full_name()} "
                f"on {appointment.appointment_date.strftime('%B %d, %Y')} "
                f"at {appointment.start_time.strftime('%I:%M %p')} has been confirmed.",
                appointment=appointment,
                priority="normal",
            )
        except Exception as e:
            self.logger.error(f"Failed to send appointment confirmed notification: {e}")

    def send_appointment_cancelled_notification(self, appointment, cancelled_by):
        """Send notification when appointment is cancelled."""
        try:
            # Determine who to notify
            if cancelled_by == appointment.patient:
                recipient = appointment.doctor
                message = (
                    f"Appointment with {appointment.patient.get_full_name()} "
                    f"on {appointment.appointment_date.strftime('%B %d, %Y')} "
                    f"at {appointment.start_time.strftime('%I:%M %p')} has been cancelled by the patient."
                )
            else:
                recipient = appointment.patient
                message = (
                    f"Your appointment with Dr. {appointment.doctor.get_full_name()} "
                    f"on {appointment.appointment_date.strftime('%B %d, %Y')} "
                    f"at {appointment.start_time.strftime('%I:%M %p')} has been cancelled."
                )

            self.create_notification(
                user=recipient,
                notification_type="appointment_cancelled",
                title="Appointment Cancelled",
                message=message,
                appointment=appointment,
                priority="high",
            )
        except Exception as e:
            self.logger.error(f"Failed to send appointment cancelled notification: {e}")

    def send_appointment_reminder(self, appointment, hours_before=24):
        """Send appointment reminder."""
        try:
            self.create_notification(
                user=appointment.patient,
                notification_type="appointment_reminder",
                title=f"Appointment Reminder - {hours_before}h",
                message=f"Reminder: You have an appointment with Dr. {appointment.doctor.get_full_name()} "
                f"tomorrow at {appointment.start_time.strftime('%I:%M %p')} "
                f"for {appointment.get_appointment_type_display()}.",
                appointment=appointment,
                priority="normal",
            )
        except Exception as e:
            self.logger.error(f"Failed to send appointment reminder: {e}")

    def send_medical_record_notification(self, medical_record):
        """Send notification when medical record is updated."""
        try:
            self.create_notification(
                user=medical_record.patient,
                notification_type="medical_record_updated",
                title="Medical Record Updated",
                message=f"Your medical record from your appointment with "
                f"Dr. {medical_record.doctor.get_full_name()} "
                f"on {medical_record.appointment.appointment_date.strftime('%B %d, %Y')} has been updated.",
                appointment=medical_record.appointment,
                priority="normal",
            )
        except Exception as e:
            # Log error but don't propagate to prevent booking failure
            self.logger.error(f"Failed to send_medical_record_notification: {e}")

    def schedule_appointment_reminders(self, appointment):
        """Schedule reminders for an appointment."""
        preferences = self.get_user_preferences(appointment.patient)
        reminder_hours = preferences.reminder_hours or [
            24,
            2,
        ]  # Default: 24h and 2h before

        for hours in reminder_hours:
            reminder_time = timezone.make_aware(
                timezone.datetime.combine(
                    appointment.appointment_date, appointment.start_time
                )
            ) - timedelta(hours=hours)

            # Only schedule if reminder time is in the future
            if reminder_time > timezone.now():
                self.create_notification(
                    user=appointment.patient,
                    notification_type="appointment_reminder",
                    title=f"Appointment Reminder - {hours}h",
                    message=f"You have an appointment with Dr. {appointment.doctor.get_full_name()} in {hours} hours",
                    appointment=appointment,
                    scheduled_for=reminder_time,
                    priority="normal",
                )

    def get_user_notifications(self, user, unread_only=False, limit=None):
        """Get notifications for a user."""
        cache_key = f"user_notifications:{user.id}:{'unread' if unread_only else 'all'}:{limit or 'all'}"

        def get_notifications():
            queryset = Notification.objects.filter(user=user)

            if unread_only:
                queryset = queryset.filter(is_read=False)

            queryset = queryset.select_related("appointment")

            if limit:
                queryset = queryset[:limit]

            return list(queryset)

        return self.get_cached(cache_key, get_notifications, timeout=300)

    def mark_as_read(self, notification_ids, user):
        """Mark notifications as read."""
        with transaction.atomic():
            notifications = Notification.objects.filter(
                id__in=notification_ids, user=user, is_read=False
            )

            for notification in notifications:
                notification.mark_as_read()

            # Clear cache
            cache.delete(f"user_notifications:{user.id}")

            return notifications.count()

    def get_user_preferences(self, user):
        """Get or create user notification preferences."""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                "reminder_hours": [24, 2],  # Default reminders
            },
        )
        return preferences

    def update_user_preferences(self, user, preferences_data):
        """Update user notification preferences."""
        preferences = self.get_user_preferences(user)

        for key, value in preferences_data.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)

        preferences.save()
        return preferences
