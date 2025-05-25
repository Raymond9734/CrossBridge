from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def clear_user_cache(sender, instance, **kwargs):
    """Clear user-related cache when user is updated."""
    try:
        from app.core.services import CacheService

        CacheService.invalidate_user_cache(instance.id)
        logger.debug(f"Cleared cache for user {instance.id}")
    except Exception as e:
        logger.warning(f"Failed to clear user cache: {e}")


@receiver(pre_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """Clean up user-related data before deletion."""
    logger.info(f"Cleaning up data for user {instance.id}")

    # Clear cache
    try:
        from app.core.services import CacheService

        CacheService.invalidate_user_cache(instance.id)
    except Exception as e:
        logger.warning(f"Failed to clear user cache on deletion: {e}")
