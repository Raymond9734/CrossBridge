# core/services.py - Updated CacheService with fallback handling

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
    """Base service class that provides common functionality."""

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
        try:
            result = cache.get(cache_key)
            if result is None:
                result = queryset_func()
                cache.set(cache_key, result, timeout)
            return result
        except Exception as e:
            # Cache failed, execute function directly
            logger.warning(f"Cache operation failed: {e}")
            return queryset_func()


class CacheService:
    """Service for managing cache operations with backend compatibility."""

    @staticmethod
    def _is_redis_backend():
        """Check if Redis is being used as cache backend."""
        try:
            backend = settings.CACHES["default"]["BACKEND"]
            return "redis" in backend.lower()
        except (KeyError, AttributeError):
            return False

    @staticmethod
    def _safe_cache_operation(operation, *args, **kwargs):
        """Safely execute cache operations with error handling."""
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Cache operation failed: {e}")
            return None

    @staticmethod
    def _safe_delete_pattern(pattern):
        """Safely delete cache keys by pattern, compatible with different backends."""
        if CacheService._is_redis_backend():
            try:
                # Redis-specific deletion with pattern matching
                keys = cache.keys(pattern)
                if keys:  # Check if keys is not None or empty
                    cache.delete_many(keys)
                    return len(keys)
            except (AttributeError, TypeError, Exception) as e:
                logger.warning(f"Redis pattern deletion failed: {e}")
        return 0

    @staticmethod
    def _safe_delete_keys(keys):
        """Safely delete specific cache keys."""
        deleted_count = 0
        for key in keys:
            try:
                if cache.delete(key):
                    deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete cache key {key}: {e}")
        return deleted_count

    @staticmethod
    def safe_cache_get(key, default=None):
        """Safely get value from cache."""
        return CacheService._safe_cache_operation(cache.get, key, default)

    @staticmethod
    def safe_cache_set(key, value, timeout=300):
        """Safely set value in cache."""
        return CacheService._safe_cache_operation(cache.set, key, value, timeout)

    @staticmethod
    def safe_cache_delete(key):
        """Safely delete key from cache."""
        return CacheService._safe_cache_operation(cache.delete, key)

    @staticmethod
    def invalidate_user_cache(user_id):
        """Invalidate all cache entries for a user."""
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

        deleted_count = CacheService._safe_delete_keys(cache_keys)
        logger.info(f"Invalidated {deleted_count} cache keys for user {user_id}")

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

        # Also clear available slots for multiple dates
        import datetime

        today = datetime.date.today()
        for i in range(30):  # Clear next 30 days
            date = today + datetime.timedelta(days=i)
            cache_keys.append(f"available_slots:{doctor_id}:{date}")

        deleted_count = CacheService._safe_delete_keys(cache_keys)
        logger.info(f"Invalidated {deleted_count} cache keys for doctor {doctor_id}")

    @staticmethod
    def invalidate_appointment_cache(patient_id, doctor_id):
        """Invalidate appointment-related cache."""
        CacheService.invalidate_user_cache(patient_id)
        CacheService.invalidate_doctor_cache(doctor_id)

    @staticmethod
    def clear_all_cache():
        """Clear all cache (use with caution)."""
        try:
            cache.clear()
            logger.info("Cleared all cache")
        except Exception as e:
            logger.warning(f"Failed to clear all cache: {e}")

    @staticmethod
    def get_cache_info():
        """Get information about current cache backend."""
        try:
            backend = settings.CACHES["default"]["BACKEND"]
            is_redis = CacheService._is_redis_backend()

            # Test cache operation
            test_key = "cache_test"
            CacheService.safe_cache_set(test_key, "test_value", 10)
            test_result = CacheService.safe_cache_get(test_key)
            CacheService.safe_cache_delete(test_key)

            return {
                "backend": backend,
                "is_redis": is_redis,
                "is_working": test_result == "test_value",
                "status": "healthy" if test_result == "test_value" else "degraded",
            }
        except Exception as e:
            return {
                "backend": "unknown",
                "is_redis": False,
                "is_working": False,
                "status": "failed",
                "error": str(e),
            }
