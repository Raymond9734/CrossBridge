from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.cache import cache
from .models import Notification, NotificationPreference


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Create notification preferences when user is created."""
    if created:
        NotificationPreference.objects.get_or_create(user=instance)


@receiver(post_save, sender=Notification)
def clear_notification_cache(sender, instance, **kwargs):
    """Clear notification cache when notification is saved."""
    cache_keys = [
        f"user_notifications:{instance.user.id}:all:*",
        f"user_notifications:{instance.user.id}:unread:*",
    ]
    
    for cache_key in cache_keys:
        cache.delete_many(cache.keys(cache_key))