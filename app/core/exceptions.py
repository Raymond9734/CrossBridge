# apps/core/exceptions.py
"""
Custom exceptions for the CareBridge application.
"""

from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class CareBridgeException(Exception):
    """Base exception for CareBridge application."""

    default_message = "An error occurred"
    default_code = "error"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message=None, code=None, status_code=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.status_code = status_code or self.status_code
        super().__init__(self.message)


class ValidationError(CareBridgeException):
    """Validation error exception."""

    default_message = "Validation failed"
    default_code = "validation_error"
    status_code = status.HTTP_400_BAD_REQUEST


class PermissionDeniedError(CareBridgeException):
    """Permission denied exception."""

    default_message = "Permission denied"
    default_code = "permission_denied"
    status_code = status.HTTP_403_FORBIDDEN


class NotFoundError(CareBridgeException):
    """Not found exception."""

    default_message = "Resource not found"
    default_code = "not_found"
    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(CareBridgeException):
    """Conflict exception."""

    default_message = "Conflict occurred"
    default_code = "conflict"
    status_code = status.HTTP_409_CONFLICT


class RateLimitExceededError(CareBridgeException):
    """Rate limit exceeded exception."""

    default_message = "Rate limit exceeded"
    default_code = "rate_limit_exceeded"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


def custom_exception_handler(exc, context):
    """
    Custom exception handler for CareBridge application.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if isinstance(exc, CareBridgeException):
        custom_response_data = {
            "error": {
                "code": exc.code,
                "message": exc.message,
                "timestamp": timezone.now().isoformat(),
                "path": context["request"].path,
            }
        }
        response = Response(custom_response_data, status=exc.status_code)

    # Log the exception
    if response is not None:
        logger.error(
            f"Exception in {context['view'].__class__.__name__}: {exc}",
            extra={
                "request": context["request"],
                "view": context["view"],
                "exception": exc,
            },
        )

    return response
