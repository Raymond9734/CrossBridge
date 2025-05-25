from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Notification, NotificationPreference
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Create notification preferences when user is created."""
    if created:
        NotificationPreference.objects.get_or_create(user=instance)


@receiver(post_save, sender=Notification)
def clear_notification_cache(sender, instance, **kwargs):
    """Clear notification cache when notification is saved."""
    try:
        from app.core.services import CacheService

        CacheService.invalidate_user_cache(instance.user.id)
    except Exception as e:
        logger.warning(f"Failed to clear notification cache: {e}")
