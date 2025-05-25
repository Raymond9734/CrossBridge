from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Appointment, DoctorAvailability
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Appointment)
def clear_appointment_cache(sender, instance, **kwargs):
    """Clear appointment-related cache when appointment is saved."""
    try:
        from app.core.services import CacheService

        CacheService.invalidate_appointment_cache(
            instance.patient.id, instance.doctor.id
        )
    except Exception as e:
        logger.warning(f"Failed to clear appointment cache: {e}")


@receiver(post_delete, sender=Appointment)
def clear_appointment_cache_on_delete(sender, instance, **kwargs):
    """Clear appointment-related cache when appointment is deleted."""
    clear_appointment_cache(sender, instance)


@receiver(post_save, sender=DoctorAvailability)
def clear_availability_cache(sender, instance, **kwargs):
    """Clear availability cache when availability is updated."""
    try:
        from app.core.services import CacheService

        doctor_id = instance.doctor.user_profile.user.id
        CacheService.invalidate_doctor_cache(doctor_id)
    except Exception as e:
        logger.warning(f"Failed to clear availability cache: {e}")
