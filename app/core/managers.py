# apps/core/managers.py
"""
Custom managers for the CareBridge application.
"""

from django.db import models
from django.db.models.query import QuerySet
from django.utils import timezone


class SoftDeleteQuerySet(QuerySet):
    """
    Custom QuerySet that filters out soft-deleted objects by default.
    """

    def delete(self):
        """Soft delete all objects in the queryset."""
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        """Permanently delete all objects in the queryset."""
        return super().delete()

    def alive(self):
        """Return only non-deleted objects."""
        return self.filter(is_deleted=False)

    def dead(self):
        """Return only deleted objects."""
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """
    Custom manager that uses SoftDeleteQuerySet.
    """

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    def all_with_deleted(self):
        """Return all objects including deleted ones."""
        return SoftDeleteQuerySet(self.model, using=self._db)

    def deleted_only(self):
        """Return only deleted objects."""
        return SoftDeleteQuerySet(self.model, using=self._db).dead()


class CacheableManager(models.Manager):
    """
    Manager that provides caching capabilities.
    """

    def get_cached(self, cache_key, timeout=300):
        """Get object from cache or database."""
        from django.core.cache import cache

        result = cache.get(cache_key)
        if result is None:
            result = self.get_queryset()
            cache.set(cache_key, result, timeout)
        return result
