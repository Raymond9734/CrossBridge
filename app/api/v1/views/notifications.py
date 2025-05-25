# api/v1/views/notifications.py
"""
Notification management ViewSets for API v1
"""

from rest_framework.decorators import action
from rest_framework import status, permissions

from .base import BaseModelViewSet
from app.notification.models import Notification, NotificationPreference
from app.notification.serializers import (
    NotificationSerializer,
    NotificationPreferenceSerializer,
)
from app.notification.services import NotificationService

import logging

logger = logging.getLogger(__name__)


class NotificationViewSet(BaseModelViewSet):
    """ViewSet for notifications."""

    serializer_class = NotificationSerializer

    def get_queryset(self):
        """Get notifications for current user."""
        queryset = Notification.objects.filter(user=self.request.user)

        # Filter by read status
        unread_only = self.request.query_params.get("unread_only")
        if unread_only == "true":
            queryset = queryset.filter(is_read=False)

        return queryset.select_related("appointment")

    def list(self, request):
        """List notifications with proper response format."""
        try:
            queryset = self.get_queryset()

            notifications_data = []
            for notification in queryset[:50]:
                notifications_data.append(
                    {
                        "id": notification.id,
                        "type": notification.notification_type,
                        "priority": notification.priority,
                        "title": notification.title,
                        "message": notification.message,
                        "is_read": notification.is_read,
                        "read_at": (
                            notification.read_at.isoformat()
                            if notification.read_at
                            else None
                        ),
                        "created_at": notification.created_at.isoformat(),
                        "appointment_id": (
                            notification.appointment.id
                            if notification.appointment
                            else None
                        ),
                    }
                )

            return self.success_response(
                data={
                    "notifications": notifications_data,
                    "unread_count": queryset.filter(is_read=False).count(),
                }
            )

        except Exception as e:
            return self.handle_exception(e, "Unable to load notifications")

    def get_permissions(self):
        """Users can only view/update their own notifications."""
        if self.action in ["create", "destroy"]:
            # Only system can create/delete notifications
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [self.permission_classes[0]]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        try:
            notification_service = NotificationService()

            notification_ids = request.data.get("notification_ids", [])
            if not notification_ids:
                # Mark all unread notifications as read
                notification_ids = list(
                    Notification.objects.filter(
                        user=request.user, is_read=False
                    ).values_list("id", flat=True)
                )

            count = notification_service.mark_as_read(notification_ids, request.user)

            return self.success_response(
                data={"count": count}, message=f"Marked {count} notifications as read"
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to mark notifications as read")

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        """Mark specific notification as read."""
        try:
            notification = self.get_object()
            notification.mark_as_read()

            return self.success_response(message="Notification marked as read")

        except Exception as e:
            return self.handle_exception(e, "Failed to mark notification as read")

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        """Get count of unread notifications."""
        try:
            count = Notification.objects.filter(
                user=request.user, is_read=False
            ).count()

            return self.success_response(data={"unread_count": count})

        except Exception as e:
            return self.handle_exception(e, "Failed to get unread count")

    @action(detail=False, methods=["get"])
    def recent(self, request):
        """Get recent notifications."""
        try:
            limit = int(request.query_params.get("limit", 10))
            notifications = Notification.objects.filter(user=request.user).order_by(
                "-created_at"
            )[:limit]

            notifications_data = []
            for notification in notifications:
                notifications_data.append(
                    {
                        "id": notification.id,
                        "type": notification.notification_type,
                        "title": notification.title,
                        "message": notification.message,
                        "is_read": notification.is_read,
                        "created_at": notification.created_at.isoformat(),
                        "time_ago": self._get_time_ago(notification.created_at),
                    }
                )

            return self.success_response(data={"notifications": notifications_data})

        except Exception as e:
            return self.handle_exception(e, "Failed to get recent notifications")

    @action(detail=False, methods=["delete"])
    def clear_all(self, request):
        """Clear all read notifications."""
        try:
            count = Notification.objects.filter(user=request.user, is_read=True).count()

            Notification.objects.filter(user=request.user, is_read=True).delete()

            return self.success_response(message=f"Cleared {count} read notifications")

        except Exception as e:
            return self.handle_exception(e, "Failed to clear notifications")

    def _get_time_ago(self, created_at):
        """Get human-readable time ago string."""
        from django.utils import timezone

        now = timezone.now()
        diff = now - created_at

        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"


class NotificationPreferenceViewSet(BaseModelViewSet):
    """ViewSet for notification preferences."""

    serializer_class = NotificationPreferenceSerializer

    def get_queryset(self):
        """Get preferences for current user."""
        return NotificationPreference.objects.filter(user=self.request.user)

    def get_object(self):
        """Get or create preferences for current user."""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preferences

    def list(self, request):
        """Get current user's notification preferences."""
        try:
            preferences = self.get_object()
            return self.success_response(
                data={"preferences": NotificationPreferenceSerializer(preferences).data}
            )
        except Exception as e:
            return self.handle_exception(e, "Failed to load preferences")

    def update(self, request, pk=None):
        """Update notification preferences."""
        try:
            preferences = self.get_object()
            serializer = self.get_serializer(
                preferences, data=request.data, partial=True
            )

            if serializer.is_valid():
                serializer.save()
                return self.success_response(
                    data={"preferences": serializer.data},
                    message="Preferences updated successfully",
                )

            return self.error_response(
                "Validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to update preferences")

    @action(detail=False, methods=["post"])
    def reset_to_defaults(self, request):
        """Reset preferences to default values."""
        try:
            preferences = self.get_object()

            # Reset to default values
            preferences.email_notifications = True
            preferences.sms_notifications = False
            preferences.push_notifications = True
            preferences.appointment_reminders = True
            preferences.appointment_confirmations = True
            preferences.medical_record_updates = True
            preferences.prescription_notifications = True
            preferences.lab_result_notifications = True
            preferences.review_requests = True
            preferences.system_messages = True
            preferences.reminder_hours = [24, 2]  # Default reminders
            preferences.quiet_hours_start = None
            preferences.quiet_hours_end = None
            preferences.max_daily_notifications = 10

            preferences.save()

            return self.success_response(
                data={
                    "preferences": NotificationPreferenceSerializer(preferences).data
                },
                message="Preferences reset to defaults",
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to reset preferences")

    @action(detail=False, methods=["post"])
    def disable_all(self, request):
        """Disable all notifications."""
        try:
            preferences = self.get_object()

            # Disable all notification types
            preferences.email_notifications = False
            preferences.sms_notifications = False
            preferences.push_notifications = False
            preferences.appointment_reminders = False
            preferences.appointment_confirmations = False
            preferences.medical_record_updates = False
            preferences.prescription_notifications = False
            preferences.lab_result_notifications = False
            preferences.review_requests = False
            preferences.system_messages = False

            preferences.save()

            return self.success_response(message="All notifications disabled")

        except Exception as e:
            return self.handle_exception(e, "Failed to disable notifications")

    @action(detail=False, methods=["post"])
    def enable_all(self, request):
        """Enable all notifications."""
        try:
            preferences = self.get_object()

            # Enable all notification types
            preferences.email_notifications = True
            preferences.sms_notifications = False  # Keep SMS disabled by default
            preferences.push_notifications = True
            preferences.appointment_reminders = True
            preferences.appointment_confirmations = True
            preferences.medical_record_updates = True
            preferences.prescription_notifications = True
            preferences.lab_result_notifications = True
            preferences.review_requests = True
            preferences.system_messages = True

            preferences.save()

            return self.success_response(message="All notifications enabled")

        except Exception as e:
            return self.handle_exception(e, "Failed to enable notifications")

    @action(detail=False, methods=["post"])
    def test_notification(self, request):
        """Send a test notification to verify settings."""
        try:
            notification_service = NotificationService()

            notification = notification_service.create_notification(
                user=request.user,
                notification_type="system_message",
                title="Test Notification",
                message="This is a test notification to verify your settings are working correctly.",
                priority="normal",
            )

            return self.success_response(
                data={"notification_id": notification.id},
                message="Test notification sent",
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to send test notification")
