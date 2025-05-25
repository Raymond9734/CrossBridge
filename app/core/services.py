"""
Base service classes for business logic.
"""

from abc import ABC, abstractmethod
from django.core.cache import cache
from django.db import transaction
from .exceptions import NotFoundError
import logging

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """
    Base service class that provides common functionality.
    """

    def __init__(self):
        self.logger = logger

    @abstractmethod
    def get_model(self):
        """Return the model class this service operates on."""
        pass

    def get_object(self, **kwargs):
        """Get a single object by criteria."""
        try:
            return self.get_model().objects.get(**kwargs)
        except self.get_model().DoesNotExist:
            raise NotFoundError(f"{self.get_model().__name__} not found")

    def get_or_create(self, defaults=None, **kwargs):
        """Get or create an object."""
        return self.get_model().objects.get_or_create(defaults=defaults, **kwargs)

    def create(self, **kwargs):
        """Create a new object."""
        with transaction.atomic():
            instance = self.get_model().objects.create(**kwargs)
            self.logger.info(
                f"Created {self.get_model().__name__} with id {instance.id}"
            )
            return instance

    def update(self, instance, **kwargs):
        """Update an existing object."""
        with transaction.atomic():
            for key, value in kwargs.items():
                setattr(instance, key, value)
            instance.save()
            self.logger.info(
                f"Updated {self.get_model().__name__} with id {instance.id}"
            )
            return instance

    def delete(self, instance):
        """Delete an object (soft delete if supported)."""
        if hasattr(instance, "is_deleted"):
            instance.delete()  # This will trigger soft delete
            self.logger.info(
                f"Soft deleted {self.get_model().__name__} with id {instance.id}"
            )
        else:
            instance.delete()
            self.logger.info(f"Hard deleted {self.get_model().__name__}")

    def get_cached(self, cache_key, queryset_func, timeout=300):
        """Get cached data from cache or execute function."""
        result = cache.get(cache_key)
        if result is None:
            result = queryset_func()
            cache.set(cache_key, result, timeout)
        return result


class CacheService:
    """
    Service for managing cache operations compatible with all Django cache backends.
    """

    @staticmethod
    def _get_known_cache_keys(user_id):
        """Get list of known cache keys for a user (no pattern matching needed)."""
        import datetime

        keys = [
            f"user_data:{user_id}",
            f"notifications:{user_id}",
            f"user_appointments:{user_id}:all",
            f"user_appointments:{user_id}:pending",
            f"user_appointments:{user_id}:confirmed",
            f"user_appointments:{user_id}:completed",
            f"user_medical_records:{user_id}:all",
            f"patient_appointments:{user_id}:all",
            f"patient_appointments:{user_id}:confirmed",
            f"patient_medical_records:{user_id}:all",
        ]

        # Add date-based keys for common date ranges
        today = datetime.date.today()
        for i in range(7):  # Clear cache for next 7 days
            date = today + datetime.timedelta(days=i)
            keys.extend(
                [
                    f"user_appointments:{user_id}:{date}",
                    f"patient_appointments:{user_id}:{date}",
                ]
            )

        # Add numbered variations for limits
        for limit in [5, 10, 20, 50]:
            keys.extend(
                [
                    f"user_medical_records:{user_id}:{limit}",
                    f"patient_medical_records:{user_id}:{limit}",
                ]
            )

        return keys

    @staticmethod
    def _get_known_doctor_keys(doctor_id):
        """Get list of known cache keys for a doctor."""
        import datetime

        keys = [
            f"doctor_availability:{doctor_id}",
            f"doctor_appointments:{doctor_id}:all",
            f"doctor_appointments:{doctor_id}:today",
            f"doctor_patients:{doctor_id}",
            f"doctor_medical_records:{doctor_id}:all",
            f"doctor_patient_stats:{doctor_id}",
            "doctors_by_specialty:all",
            "available_doctors:all",
        ]

        # Add available slots for next 30 days
        today = datetime.date.today()
        for i in range(30):
            date = today + datetime.timedelta(days=i)
            keys.append(f"available_slots:{doctor_id}:{date}")

        # Add numbered variations
        for limit in [10, 20, 50]:
            keys.append(f"doctor_medical_records:{doctor_id}:{limit}")

        # Add specialty-based keys
        specialties = [
            "General Medicine",
            "Cardiology",
            "Dermatology",
            "Pediatrics",
            "Orthopedics",
            "Gynecology",
            "Internal Medicine",
            "Surgery",
            "Psychiatry",
            "Radiology",
            "Anesthesiology",
            "Emergency Medicine",
        ]
        for specialty in specialties:
            keys.append(f"doctors_by_specialty:{specialty}")

        return keys

    @staticmethod
    def _safe_delete_keys(keys):
        """Safely delete specific cache keys."""
        deleted_count = 0
        for key in keys:
            try:
                result = cache.delete(key)
                if result:  # Some backends return True/False for success
                    deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete cache key {key}: {e}")

        if deleted_count > 0:
            logger.debug(f"Deleted {deleted_count} cache keys")

    @staticmethod
    def invalidate_user_cache(user_id):
        """Invalidate all cache entries for a user."""
        cache_keys = CacheService._get_known_cache_keys(user_id)
        CacheService._safe_delete_keys(cache_keys)

    @staticmethod
    def invalidate_doctor_cache(doctor_id):
        """Invalidate cache entries for a doctor."""
        cache_keys = CacheService._get_known_doctor_keys(doctor_id)
        CacheService._safe_delete_keys(cache_keys)

    @staticmethod
    def invalidate_appointment_cache(patient_id, doctor_id):
        """Invalidate appointment-related cache."""
        # Combine both user cache invalidations
        patient_keys = CacheService._get_known_cache_keys(patient_id)
        doctor_keys = CacheService._get_known_doctor_keys(doctor_id)

        # Add appointment-specific keys
        appointment_keys = [
            f"patient_appointments:{patient_id}:all",
            f"patient_appointments:{patient_id}:pending",
            f"patient_appointments:{patient_id}:confirmed",
            f"doctor_appointments:{doctor_id}:all",
            f"doctor_appointments:{doctor_id}:today",
        ]

        all_keys = list(set(patient_keys + doctor_keys + appointment_keys))
        CacheService._safe_delete_keys(all_keys)

    @staticmethod
    def clear_all_cache():
        """Clear all cache (use with caution)."""
        try:
            cache.clear()
            logger.info("All cache cleared successfully")
        except Exception as e:
            logger.warning(f"Failed to clear all cache: {e}")

    @staticmethod
    def get_cache_stats():
        """Get cache statistics if available."""
        try:
            # This works with some backends like Redis, but not all
            if hasattr(cache, "_cache") and hasattr(cache._cache, "info"):
                return cache._cache.info()
        except Exception:
            pass

        return {"message": "Cache stats not available for this backend"}

    @staticmethod
    def invalidate_system_cache():
        """Invalidate system-wide cache keys."""
        system_keys = [
            "system_stats",
            "available_doctors:all",
            "doctors_by_specialty:all",
            "system_notifications",
            "global_settings",
        ]
        CacheService._safe_delete_keys(system_keys)
