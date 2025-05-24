# apps/core/signals.py
"""
Signal handlers for the core application.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def clear_user_cache(sender, instance, **kwargs):
    """Clear user-related cache when user is updated."""
    cache_keys = [
        f"user:{instance.id}:*",
        f"user_profile:{instance.id}",
        f"user_appointments:{instance.id}",
    ]

    for key_pattern in cache_keys:
        # Clear cache entries related to this user
        cache.delete_many(cache.keys(key_pattern))

    logger.info(f"Cleared cache for user {instance.id}")


@receiver(pre_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """Clean up user-related data before deletion."""
    logger.info(f"Cleaning up data for user {instance.id}")

    # Clear cache
    clear_user_cache(sender, instance)

    # Additional cleanup logic can be added here
