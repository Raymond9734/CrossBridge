from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import MedicalRecord


@receiver(post_save, sender=MedicalRecord)
def clear_medical_record_cache(sender, instance, **kwargs):
    """Clear medical record cache when record is saved."""
    cache_keys = [
        f"patient_medical_records:{instance.patient.id}:*",
        f"doctor_medical_records:{instance.doctor.id}:*",
    ]

    for key_pattern in cache_keys:
        cache.delete_many(cache.keys(key_pattern))
