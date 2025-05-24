from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Appointment, DoctorAvailability


@receiver(post_save, sender=Appointment)
def clear_appointment_cache(sender, instance, **kwargs):
    """Clear appointment-related cache when appointment is saved."""
    cache_keys = [
        f"patient_appointments:{instance.patient.id}:*",
        f"doctor_appointments:{instance.doctor.id}:*",
        f"available_slots:{instance.doctor.id}:*",
    ]
    
    for key_pattern in cache_keys:
        cache.delete_many(cache.keys(key_pattern))


@receiver(post_delete, sender=Appointment)
def clear_appointment_cache_on_delete(sender, instance, **kwargs):
    """Clear appointment-related cache when appointment is deleted."""
    clear_appointment_cache(sender, instance)


@receiver(post_save, sender=DoctorAvailability)
def clear_availability_cache(sender, instance, **kwargs):
    """Clear availability cache when availability is updated."""
    doctor_id = instance.doctor.user_profile.user.id
    cache_keys = [
        f"doctor_availability:{doctor_id}",
        f"available_slots:{doctor_id}:*",
    ]
    
    for key_pattern in cache_keys:
        cache.delete_many(cache.keys(key_pattern))