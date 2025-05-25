"""
Custom middleware for the CareBridge application.
"""

from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.http import JsonResponse
from inertia import share
from django.conf import settings
from .utils import get_client_ip
import time
import logging
import uuid

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all requests.
    """

    def process_request(self, request):
        request.start_time = time.time()
        request.request_id = str(uuid.uuid4())

        logger.info(
            f"Request started: {request.method} {request.path}",
            extra={
                "request_id": request.request_id,
                "method": request.method,
                "path": request.path,
                "user": str(request.user) if hasattr(request, "user") else "Anonymous",
                "ip": get_client_ip(request),
            },
        )

    def process_response(self, request, response):
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time
            logger.info(
                f"Request completed: {request.method} {request.path} - {response.status_code} ({duration:.3f}s)",
                extra={
                    "request_id": getattr(request, "request_id", "unknown"),
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "duration": duration,
                },
            )
        return response


class PerformanceMiddleware(MiddlewareMixin):
    """
    Middleware to monitor performance and add performance headers.
    """

    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time
            response["X-Response-Time"] = f"{duration:.3f}s"

            # Log slow requests
            if duration > 1.0:  # Log requests taking more than 1 second
                logger.warning(
                    f"Slow request detected: {request.method} {request.path} took {duration:.3f}s"
                )

        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Enhanced rate limiting middleware - works with any cache backend.
    """

    def process_request(self, request):
        if request.path.startswith("/api/"):
            client_ip = get_client_ip(request)

            # Different limits for different endpoints
            if "/api/v1/auth/login/" in request.path:
                limit, window = 5, 300  # 5 attempts per 5 minutes
                cache_key = f"rate_limit:login:{client_ip}"
            elif "/api/v1/appointments/" in request.path and request.method == "POST":
                limit, window = 10, 60  # 10 bookings per minute
                cache_key = f"rate_limit:appointment:{client_ip}"
            else:
                limit, window = 100, 60  # 100 requests per minute
                cache_key = f"rate_limit:general:{client_ip}"

            try:
                current_requests = cache.get(cache_key, 0)

                if current_requests >= limit:
                    return JsonResponse(
                        {"error": "Rate limit exceeded. Please try again later."},
                        status=429,
                    )

                # Increment counter with expiration
                cache.set(cache_key, current_requests + 1, window)

            except Exception as e:
                # Log cache errors but don't fail the request
                logger.warning(f"Rate limiting cache error: {e}")
                # Continue without rate limiting if cache fails


class InertiaShareMiddleware(MiddlewareMixin):
    """
    Enhanced Inertia middleware with caching and optimizations.
    """

    def process_request(self, request):
        if request.path.startswith("/api/"):
            return None  # Skip for API requests

        # Share data that should be available to all components
        share(
            request,
            app_name=getattr(settings, "APP_NAME", "CareBridge"),
            user=lambda: self._get_user_data(request),
            auth=lambda: self._get_auth_data(request),
            notifications=lambda: self._get_notifications(request),
            flash=lambda: self._get_flash_messages(request),
            meta=lambda: self._get_meta_data(request),
        )

    def _get_user_data(self, request):
        """Get cached user data."""
        if not request.user.is_authenticated:
            return None

        cache_key = f"user_data:{request.user.id}"

        try:
            user_data = cache.get(cache_key)
        except Exception as e:
            logger.warning(f"Cache error in _get_user_data: {e}")
            user_data = None

        if user_data is None:
            try:
                from app.account.models import UserProfile

                user_profile = UserProfile.objects.get(user=request.user)
                user_data = {
                    "id": request.user.id,
                    "email": request.user.email,
                    "name": request.user.get_full_name() or request.user.username,
                    "first_name": request.user.first_name,
                    "last_name": request.user.last_name,
                    "role": user_profile.role,
                    "phone": user_profile.phone,
                    "address": user_profile.address,
                    "emergency_contact": user_profile.emergency_contact,
                    "is_staff": request.user.is_staff,
                }

                try:
                    cache.set(cache_key, user_data, 300)  # Cache for 5 minutes
                except Exception as e:
                    logger.warning(f"Failed to cache user data: {e}")

            except Exception as e:
                logger.warning(f"Error getting user profile: {e}")
                # Fallback user data
                user_data = {
                    "id": request.user.id,
                    "email": request.user.email,
                    "name": request.user.get_full_name() or request.user.username,
                    "role": "patient",
                    "is_staff": request.user.is_staff,
                }

        return user_data

    def _get_auth_data(self, request):
        """Get authentication data with caching."""
        if not request.user.is_authenticated:
            return {
                "user": None,
                "authenticated": False,
                "role": None,
            }

        user_data = self._get_user_data(request)
        if user_data:
            return {
                "user": user_data,
                "authenticated": True,
                "role": user_data.get("role"),
            }

        return {
            "user": None,
            "authenticated": False,
            "role": None,
        }

    def _get_notifications(self, request):
        """Get user notifications with caching."""
        if not request.user.is_authenticated:
            return {"unread_count": 0, "items": []}

        cache_key = f"notifications:{request.user.id}"

        try:
            notifications_data = cache.get(cache_key)
        except Exception as e:
            logger.warning(f"Cache error in _get_notifications: {e}")
            notifications_data = None

        if notifications_data is None:
            try:
                from app.notification.models import Notification

                notifications = Notification.objects.filter(
                    user=request.user, is_read=False
                ).order_by("-created_at")[:10]

                notifications_data = {
                    "unread_count": notifications.count(),
                    "items": [
                        {
                            "id": notif.id,
                            "type": notif.notification_type,
                            "title": notif.title,
                            "message": notif.message,
                            "created_at": notif.created_at.isoformat(),
                            "is_read": notif.is_read,
                        }
                        for notif in notifications
                    ],
                }

                try:
                    cache.set(cache_key, notifications_data, 60)  # Cache for 1 minute
                except Exception as e:
                    logger.warning(f"Failed to cache notifications: {e}")

            except Exception as e:
                logger.warning(f"Error getting notifications: {e}")
                notifications_data = {"unread_count": 0, "items": []}

        return notifications_data

    def _get_flash_messages(self, request):
        """Get Django messages for toast notifications."""
        try:
            from django.contrib import messages

            flash_messages = []
            storage = messages.get_messages(request)

            for message in storage:
                flash_messages.append(
                    {
                        "message": str(message),
                        "level": message.level_tag,
                        "tags": message.tags,
                    }
                )

            return flash_messages
        except Exception as e:
            logger.warning(f"Error getting flash messages: {e}")
            return []

    def _get_meta_data(self, request):
        """Get meta data for the application."""
        return {
            "version": "1.0.0",
            "environment": "development" if settings.DEBUG else "production",
            "timestamp": time.time(),
        }
