from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MedicalRecord
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MedicalRecord)
def clear_medical_record_cache(sender, instance, **kwargs):
    """Clear medical record cache when record is saved."""
    try:
        from app.core.services import CacheService

        CacheService.invalidate_user_cache(instance.patient.id)
        CacheService.invalidate_doctor_cache(instance.doctor.id)
    except Exception as e:
        logger.warning(f"Failed to clear medical record cache: {e}")
