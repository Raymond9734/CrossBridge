from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from app.core.services import BaseService
from app.core.exceptions import ValidationError
from .models import Notification, NotificationTemplate, NotificationPreference
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

    def create_from_template(self, user, template_name, context, **kwargs):
        """Create notification from template."""
        try:
            template = NotificationTemplate.objects.get(
                name=template_name, is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            raise ValidationError(f"Notification template '{template_name}' not found")

        title, message = template.render(context)

        # Use template defaults for delivery channels if not specified
        delivery_channels = kwargs.pop("delivery_channels", None)
        if delivery_channels is None:
            delivery_channels = []
            if template.default_send_email:
                delivery_channels.append("email")
            if template.default_send_sms:
                delivery_channels.append("sms")
            if template.default_send_push:
                delivery_channels.append("push")

        return self.create_notification(
            user=user,
            notification_type=template.notification_type,
            title=title,
            message=message,
            delivery_channels=delivery_channels,
            **kwargs,
        )

    def send_appointment_request_notification(self, appointment):
        """Send notification when appointment is requested."""
        context = {
            "patient_name": appointment.patient.get_full_name(),
            "doctor_name": f"Dr. {appointment.doctor.get_full_name()}",
            "appointment_date": appointment.appointment_date.strftime("%B %d, %Y"),
            "appointment_time": appointment.start_time.strftime("%I:%M %p"),
            "appointment_type": appointment.get_appointment_type_display(),
        }

        # Notify doctor
        self.create_from_template(
            user=appointment.doctor,
            template_name="appointment_request",
            context=context,
            appointment=appointment,
            priority="normal",
        )

    def send_appointment_confirmed_notification(self, appointment):
        """Send notification when appointment is confirmed."""
        context = {
            "patient_name": appointment.patient.get_full_name(),
            "doctor_name": f"Dr. {appointment.doctor.get_full_name()}",
            "appointment_date": appointment.appointment_date.strftime("%B %d, %Y"),
            "appointment_time": appointment.start_time.strftime("%I:%M %p"),
            "appointment_type": appointment.get_appointment_type_display(),
        }

        # Notify patient
        self.create_from_template(
            user=appointment.patient,
            template_name="appointment_confirmed",
            context=context,
            appointment=appointment,
            priority="normal",
        )

    def send_appointment_cancelled_notification(self, appointment, cancelled_by):
        """Send notification when appointment is cancelled."""
        context = {
            "patient_name": appointment.patient.get_full_name(),
            "doctor_name": f"Dr. {appointment.doctor.get_full_name()}",
            "appointment_date": appointment.appointment_date.strftime("%B %d, %Y"),
            "appointment_time": appointment.start_time.strftime("%I:%M %p"),
            "cancelled_by": cancelled_by.get_full_name() if cancelled_by else "System",
        }

        # Notify the other party
        if cancelled_by == appointment.patient:
            recipient = appointment.doctor
        else:
            recipient = appointment.patient

        self.create_from_template(
            user=recipient,
            template_name="appointment_cancelled",
            context=context,
            appointment=appointment,
            priority="high",
        )

    def send_appointment_reminder(self, appointment, hours_before=24):
        """Send appointment reminder."""
        context = {
            "patient_name": appointment.patient.get_full_name(),
            "doctor_name": f"Dr. {appointment.doctor.get_full_name()}",
            "appointment_date": appointment.appointment_date.strftime("%B %d, %Y"),
            "appointment_time": appointment.start_time.strftime("%I:%M %p"),
            "hours_before": hours_before,
        }

        # Send to patient
        self.create_from_template(
            user=appointment.patient,
            template_name="appointment_reminder",
            context=context,
            appointment=appointment,
            priority="normal",
        )

    def send_medical_record_notification(self, medical_record):
        """Send notification when medical record is updated."""
        context = {
            "patient_name": medical_record.patient.get_full_name(),
            "doctor_name": f"Dr. {medical_record.doctor.get_full_name()}",
            "appointment_date": medical_record.appointment.appointment_date.strftime(
                "%B %d, %Y"
            ),
        }

        self.create_from_template(
            user=medical_record.patient,
            template_name="medical_record_updated",
            context=context,
            appointment=medical_record.appointment,
            priority="normal",
        )

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
