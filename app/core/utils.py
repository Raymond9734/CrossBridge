"""
Utility functions for the CareBridge application.
"""

from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
import hashlib
import functools


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a cache key based on prefix and arguments.
    """
    key_parts = [prefix]
    key_parts.extend(str(arg) for arg in args)

    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        key_parts.extend(f"{k}:{v}" for k, v in sorted_kwargs)

    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cache_result(key: str, timeout: int = 300):
    """
    Decorator to cache function results.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = generate_cache_key(key, *args, **kwargs)
            result = cache.get(cache_key)

            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)

            return result

        return wrapper

    return decorator


def get_client_ip(request):
    """
    Get the client IP address from the request.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data showing only the last few characters.
    """
    if len(data) <= visible_chars:
        return "*" * len(data)
    return "*" * (len(data) - visible_chars) + data[-visible_chars:]


def validate_file_extension(filename: str, allowed_extensions: list = None) -> bool:
    """
    Validate file extension against allowed extensions.
    """
    if allowed_extensions is None:
        allowed_extensions = settings.HEALTHCARE_SETTINGS["ALLOWED_FILE_TYPES"]

    extension = filename.split(".")[-1].lower()
    return extension in allowed_extensions


def calculate_age(birth_date):
    """
    Calculate age from birth date.
    """
    if not birth_date:
        return None

    today = timezone.now().date()
    age = today.year - birth_date.year

    # Adjust if birthday hasn't occurred this year
    if today.month < birth_date.month or (
        today.month == birth_date.month and today.day < birth_date.day
    ):
        age -= 1

    return age
