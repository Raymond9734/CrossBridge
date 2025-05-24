from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import MedicalRecord, Prescription, LabResult, Review


@receiver(post_save, sender=MedicalRecord)
def clear_medical_record_cache(sender, instance, **kwargs):
    """Clear medical record cache when record is saved."""
    cache_keys = [
        f"patient_medical_records:{instance.patient.id}:*",
        f"doctor_medical_records:{instance.doctor.id}:*",
    ]

    for key_pattern in cache_keys:
        cache.delete_many(cache.keys(key_pattern))


@receiver(post_save, sender=Prescription)
def clear_prescription_cache(sender, instance, **kwargs):
    """Clear prescription cache when prescription is saved."""
    cache.delete(f"patient_prescriptions:{instance.patient.id}")


@receiver(post_save, sender=LabResult)
def clear_lab_result_cache(sender, instance, **kwargs):
    """Clear lab result cache when result is saved."""
    cache.delete(f"patient_lab_results:{instance.medical_record.patient.id}")


@receiver(post_save, sender=Review)
def clear_review_cache(sender, instance, **kwargs):
    """Clear review cache when review is saved."""
    cache_keys = [
        f"doctor_reviews:{instance.doctor.id}:all",
        f"doctor_reviews:{instance.doctor.id}:verified",
    ]

    for key in cache_keys:
        cache.delete(key)
