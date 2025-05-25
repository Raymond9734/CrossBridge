from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def clear_user_cache(sender, instance, **kwargs):
    """Clear user-related cache when user is updated."""
    from .services import CacheService

    CacheService.invalidate_user_cache(instance.id)
    logger.info(f"Cleared cache for user {instance.id}")


@receiver(pre_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """Clean up user-related data before deletion."""
    from .services import CacheService

    CacheService.invalidate_user_cache(instance.id)
    logger.info(f"Cleaned up data for user {instance.id}")
