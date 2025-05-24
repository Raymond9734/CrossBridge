from django.utils import timezone
from app.core.managers import CacheableManager


class NotificationManager(CacheableManager):
    """Custom manager for Notification model."""

    def unread(self):
        """Get unread notifications."""
        return self.filter(is_read=False)

    def for_user(self, user):
        """Get notifications for a specific user."""
        return self.filter(user=user)

    def by_type(self, notification_type):
        """Get notifications by type."""
        return self.filter(notification_type=notification_type)

    def by_priority(self, priority):
        """Get notifications by priority."""
        return self.filter(priority=priority)

    def pending_delivery(self):
        """Get notifications that need to be sent."""
        now = timezone.now()
        return self.filter(is_sent=False, scheduled_for__lte=now).exclude(
            expires_at__lt=now
        )

    def expired(self):
        """Get expired notifications."""
        return self.filter(expires_at__lt=timezone.now())

    def recent(self, days=7):
        """Get recent notifications."""
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
