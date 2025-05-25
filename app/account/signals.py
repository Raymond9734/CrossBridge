from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved."""
    if hasattr(instance, "userprofile"):
        instance.userprofile.save()


@receiver(post_save, sender=UserProfile)
def handle_profile_updates(sender, instance, **kwargs):
    """Handle profile updates."""
    try:
        from app.core.services import CacheService

        CacheService.invalidate_user_cache(instance.user.id)

        # If doctor, clear doctor-specific cache
        if instance.role == "doctor":
            CacheService.invalidate_doctor_cache(instance.user.id)
    except Exception as e:
        logger.warning(f"Failed to clear profile cache: {e}")
