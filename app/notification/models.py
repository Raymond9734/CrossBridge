from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from app.core.models import TimeStampedModel
from app.appointment.models import Appointment
from app.notification.managers import NotificationManager


class Notification(TimeStampedModel):
    """System notifications for users"""

    NOTIFICATION_TYPES = [
        ("appointment_confirmed", "Appointment Confirmed"),
        ("appointment_reminder", "Appointment Reminder"),
        ("appointment_cancelled", "Appointment Cancelled"),
        ("appointment_rescheduled", "Appointment Rescheduled"),
        ("medical_record_updated", "Medical Record Updated"),
        ("prescription_ready", "Prescription Ready"),
        ("lab_results_available", "Lab Results Available"),
        ("follow_up_required", "Follow-up Required"),
        ("review_request", "Review Request"),
        ("system_message", "System Message"),
        ("payment_reminder", "Payment Reminder"),
        ("insurance_update", "Insurance Update"),
    ]

    PRIORITY_LEVELS = [
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    objects = NotificationManager()

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications", db_index=True
    )
    notification_type = models.CharField(
        max_length=30, choices=NOTIFICATION_TYPES, db_index=True
    )
    priority = models.CharField(
        max_length=10, choices=PRIORITY_LEVELS, default="normal", db_index=True
    )

    title = models.CharField(max_length=200)
    message = models.TextField()

    # Status fields
    is_read = models.BooleanField(default=False, db_index=True)
    is_sent = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    # Optional related objects
    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, null=True, blank=True
    )

    # Delivery channels
    send_email = models.BooleanField(default=False)
    send_sms = models.BooleanField(default=False)
    send_push = models.BooleanField(default=True)  # In-app notification

    # Scheduling
    scheduled_for = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["notification_type"]),
            models.Index(fields=["priority", "is_read"]),
            models.Index(fields=["scheduled_for"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.title} for {self.user.get_full_name()}"

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    def mark_as_sent(self):
        """Mark notification as sent."""
        if not self.is_sent:
            self.is_sent = True
            self.sent_at = timezone.now()
            self.save(update_fields=["is_sent", "sent_at"])

    @property
    def is_expired(self):
        """Check if notification has expired."""
        return self.expires_at and timezone.now() > self.expires_at

    @property
    def is_scheduled(self):
        """Check if notification is scheduled for future delivery."""
        return self.scheduled_for and timezone.now() < self.scheduled_for

    def get_delivery_channels(self):
        """Get list of delivery channels for this notification."""
        channels = []
        if self.send_push:
            channels.append("push")
        if self.send_email:
            channels.append("email")
        if self.send_sms:
            channels.append("sms")
        return channels


class NotificationPreference(TimeStampedModel):
    """User preferences for notifications"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="notification_preferences"
    )

    # Global preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)

    # Specific notification type preferences
    appointment_reminders = models.BooleanField(default=True)
    appointment_confirmations = models.BooleanField(default=True)
    medical_record_updates = models.BooleanField(default=True)
    prescription_notifications = models.BooleanField(default=True)
    lab_result_notifications = models.BooleanField(default=True)
    review_requests = models.BooleanField(default=True)
    system_messages = models.BooleanField(default=True)

    # Timing preferences
    reminder_hours = models.JSONField(
        default=list,
        help_text="Hours before appointment to send reminders (e.g., [24, 2])",
    )

    # Quiet hours
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    # Frequency limits
    max_daily_notifications = models.PositiveIntegerField(default=10)

    class Meta:
        db_table = "notification_preferences"

    def __str__(self):
        return f"Notification preferences for {self.user.get_full_name()}"

    def should_send_notification(self, notification_type, channel):
        """Check if user wants to receive this type of notification via this channel."""
        # Check global channel preference
        if channel == "email" and not self.email_notifications:
            return False
        elif channel == "sms" and not self.sms_notifications:
            return False
        elif channel == "push" and not self.push_notifications:
            return False

        # Check specific notification type preference
        type_mapping = {
            "appointment_confirmed": self.appointment_confirmations,
            "appointment_reminder": self.appointment_reminders,
            "appointment_cancelled": self.appointment_confirmations,
            "appointment_rescheduled": self.appointment_confirmations,
            "medical_record_updated": self.medical_record_updates,
            "prescription_ready": self.prescription_notifications,
            "lab_results_available": self.lab_result_notifications,
            "review_request": self.review_requests,
            "system_message": self.system_messages,
        }

        return type_mapping.get(notification_type, True)

    def is_quiet_hours(self):
        """Check if current time is within quiet hours."""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False

        current_time = timezone.now().time()

        if self.quiet_hours_start <= self.quiet_hours_end:
            # Same day quiet hours (e.g., 22:00 to 08:00)
            return self.quiet_hours_start <= current_time <= self.quiet_hours_end
        else:
            # Overnight quiet hours (e.g., 22:00 to 08:00 next day)
            return (
                current_time >= self.quiet_hours_start
                or current_time <= self.quiet_hours_end
            )
