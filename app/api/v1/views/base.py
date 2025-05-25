# api/v1/views/base.py
"""
Base view classes and common functionality for API v1
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import logging

from app.account.models import UserProfile

logger = logging.getLogger(__name__)


class BaseAPIViewSet(viewsets.ViewSet):
    """Base ViewSet with common functionality"""

    permission_classes = [IsAuthenticated]

    def get_user_profile(self, user=None):
        """Get user profile with error handling"""
        user = user or self.request.user
        try:
            return UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return None

    def success_response(self, data=None, message=None, status_code=status.HTTP_200_OK):
        """Standard success response format"""
        response_data = {"success": True}

        if message:
            response_data["message"] = message
        if data is not None:
            response_data.update(data)

        return Response(response_data, status=status_code)

    def error_response(
        self,
        error,
        status_code=status.HTTP_400_BAD_REQUEST,
        errors=None,
        error_code=None,
    ):
        """Standard error response format"""
        response_data = {"success": False, "error": error}

        if errors:
            response_data["errors"] = errors
        if error_code:
            response_data["error_code"] = error_code

        return Response(response_data, status=status_code)

    def handle_exception(self, exc, message="An error occurred"):
        """Standard exception handling"""
        logger.error(f"{self.__class__.__name__} error: {exc}")
        return self.error_response(
            message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class BaseModelViewSet(viewsets.ModelViewSet):
    """Base ModelViewSet with common functionality"""

    permission_classes = [IsAuthenticated]

    def get_user_profile(self, user=None):
        """Get user profile with error handling"""
        user = user or self.request.user
        try:
            return UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return None

    def success_response(self, data=None, message=None, status_code=status.HTTP_200_OK):
        """Standard success response format"""
        response_data = {"success": True}

        if message:
            response_data["message"] = message
        if data is not None:
            response_data.update(data)

        return Response(response_data, status=status_code)

    def error_response(
        self,
        error,
        status_code=status.HTTP_400_BAD_REQUEST,
        errors=None,
        error_code=None,
    ):
        """Standard error response format"""
        response_data = {"success": False, "error": error}

        if errors:
            response_data["errors"] = errors
        if error_code:
            response_data["error_code"] = error_code

        return Response(response_data, status=status_code)

    def handle_exception(self, exc, message="An error occurred"):
        """Standard exception handling"""
        logger.error(f"{self.__class__.__name__} error: {exc}")
        return self.error_response(
            message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def get_csrf_token():
    """Get CSRF token helper function"""
    from django.middleware.csrf import get_token
    from django.http import HttpRequest

    request = HttpRequest()
    return get_token(request)


def format_datetime(dt):
    """Format datetime for API responses"""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return None


def format_date(date):
    """Format date for API responses"""
    if date:
        return date.strftime("%Y-%m-%d")
    return None


def format_time(time):
    """Format time for API responses"""
    if time:
        return time.strftime("%I:%M %p")
    return None
