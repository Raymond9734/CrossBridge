"""
Base service classes for business logic.
"""

from abc import ABC, abstractmethod
from django.core.cache import cache
from django.db import transaction
from django.conf import settings
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
            # Don't convert to list automatically - let the caller decide
            cache.set(cache_key, result, timeout)
        return result


class CacheService:
    """
    Service for managing cache operations with backend compatibility.
    """

    @staticmethod
    def _is_redis_backend():
        """Check if Redis is being used as cache backend."""
        backend = settings.CACHES["default"]["BACKEND"]
        return "redis" in backend.lower() or "RedisCache" in backend

    @staticmethod
    def _safe_delete_pattern(pattern):
        """Safely delete cache keys by pattern, compatible with different backends."""
        if CacheService._is_redis_backend():
            try:
                # Redis-specific deletion with pattern matching
                keys = cache.keys(pattern)
                if keys:
                    cache.delete_many(keys)
            except AttributeError:
                # Fallback if keys() method doesn't exist
                pass
        else:
            # For non-Redis backends, we can't use patterns
            # Just delete specific keys we know about
            pass

    @staticmethod
    def _safe_delete_keys(keys):
        """Safely delete specific cache keys."""
        for key in keys:
            try:
                cache.delete(key)
            except Exception as e:
                logger.warning(f"Failed to delete cache key {key}: {e}")

    @staticmethod
    def invalidate_user_cache(user_id):
        """Invalidate all cache entries for a user."""
        # Use specific keys instead of patterns for LocMemCache compatibility
        cache_keys = [
            f"user_data:{user_id}",
            f"user_appointments:{user_id}:all",
            f"user_appointments:{user_id}:pending",
            f"user_appointments:{user_id}:confirmed",
            f"user_appointments:{user_id}:completed",
            f"user_medical_records:{user_id}:all",
            f"user_medical_records:{user_id}:5",
            f"user_medical_records:{user_id}:10",
            f"notifications:{user_id}",
            f"patient_appointments:{user_id}:all",
            f"patient_appointments:{user_id}:confirmed",
            f"patient_medical_records:{user_id}:all",
            f"patient_medical_records:{user_id}:5",
            f"patient_prescriptions:{user_id}:active",
            f"patient_prescriptions:{user_id}:all",
            f"patient_lab_results:{user_id}:all",
        ]

        CacheService._safe_delete_keys(cache_keys)

    @staticmethod
    def invalidate_doctor_cache(doctor_id):
        """Invalidate cache entries for a doctor."""
        cache_keys = [
            f"doctor_availability:{doctor_id}",
            f"doctor_appointments:{doctor_id}:all",
            f"doctor_appointments:{doctor_id}:today",
            f"doctor_patients:{doctor_id}",
            f"doctor_medical_records:{doctor_id}:all",
            f"doctor_medical_records:{doctor_id}:10",
            f"doctor_patient_stats:{doctor_id}",
            "doctors_by_specialty:all",
        ]

        # Also clear available slots for multiple dates (common patterns)
        import datetime

        today = datetime.date.today()
        for i in range(30):  # Clear next 30 days
            date = today + datetime.timedelta(days=i)
            cache_keys.append(f"available_slots:{doctor_id}:{date}")

        CacheService._safe_delete_keys(cache_keys)

    @staticmethod
    def invalidate_appointment_cache(patient_id, doctor_id):
        """Invalidate appointment-related cache."""
        # Combine both user cache invalidations
        CacheService.invalidate_user_cache(patient_id)
        CacheService.invalidate_doctor_cache(doctor_id)

    @staticmethod
    def clear_all_cache():
        """Clear all cache (use with caution)."""
        try:
            cache.clear()
        except Exception as e:
            logger.warning(f"Failed to clear all cache: {e}")
