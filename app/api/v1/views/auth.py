# api/v1/views/auth.py
"""
Authentication ViewSets for API v1
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from .base import BaseAPIViewSet
from app.account.models import UserProfile
from app.account.serializers import UserProfileSerializer, UserRegistrationSerializer

import logging

logger = logging.getLogger(__name__)


class AuthViewSet(BaseAPIViewSet):
    """Authentication endpoints."""

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @action(detail=False, methods=["post"])
    def login(self, request):
        """User login endpoint."""
        try:
            email = request.data.get("email")
            password = request.data.get("password")
            remember = request.data.get("remember", False)

            if not email or not password:
                return self.error_response(
                    "Email and password are required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
            except User.DoesNotExist:
                return self.error_response(
                    "Invalid credentials",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            if user and user.is_active:
                login(request, user)

                # Set session expiry
                if not remember:
                    request.session.set_expiry(0)

                # Get user profile data
                try:
                    profile = UserProfile.objects.get(user=user)
                    profile_data = UserProfileSerializer(profile).data
                except UserProfile.DoesNotExist:
                    profile_data = None

                return self.success_response(
                    data={"user": profile_data},
                    message="Login successful"
                )

            return self.error_response(
                "Invalid credentials",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        except Exception as e:
            return self.handle_exception(e, "Login failed")

    @action(detail=False, methods=["post"])
    def register(self, request):
        """User registration endpoint."""
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                login(request, user)

                # Get created profile
                profile = UserProfile.objects.get(user=user)
                profile_data = UserProfileSerializer(profile).data

                return self.success_response(
                    data={"user": profile_data},
                    message="Registration successful",
                    status_code=status.HTTP_201_CREATED
                )

            return self.error_response(
                "Registration failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )

        except Exception as e:
            return self.handle_exception(e, "Registration failed")

    @action(detail=False, methods=["post"])
    def logout(self, request):
        """User logout endpoint."""
        try:
            logout(request)
            return self.success_response(message="Logout successful")
        except Exception as e:
            return self.handle_exception(e, "Logout failed")

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Get current user profile."""
        try:
            if request.user.is_authenticated:
                try:
                    profile = UserProfile.objects.get(user=request.user)
                    return self.success_response(
                        data={"user": UserProfileSerializer(profile).data}
                    )
                except UserProfile.DoesNotExist:
                    return self.error_response(
                        "Profile not found",
                        status_code=status.HTTP_404_NOT_FOUND
                    )

            return self.error_response(
                "Not authenticated",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to get user profile")

    @action(detail=False, methods=["post"])
    def change_password(self, request):
        """Change user password."""
        try:
            if not request.user.is_authenticated:
                return self.error_response(
                    "Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            current_password = request.data.get("current_password")
            new_password = request.data.get("new_password")
            confirm_password = request.data.get("confirm_password")

            if not all([current_password, new_password, confirm_password]):
                return self.error_response(
                    "All password fields are required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if new_password != confirm_password:
                return self.error_response(
                    "New passwords do not match",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if not request.user.check_password(current_password):
                return self.error_response(
                    "Current password is incorrect",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if len(new_password) < 8:
                return self.error_response(
                    "Password must be at least 8 characters long",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            request.user.set_password(new_password)
            request.user.save()

            return self.success_response(message="Password changed successfully")

        except Exception as e:
            return self.handle_exception(e, "Failed to change password")

    @action(detail=False, methods=["post"])
    def refresh_session(self, request):
        """Refresh user session."""
        try:
            if not request.user.is_authenticated:
                return self.error_response(
                    "Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            # Update last activity
            request.session.modified = True
            
            profile = self.get_user_profile()
            if profile:
                return self.success_response(
                    data={"user": UserProfileSerializer(profile).data},
                    message="Session refreshed"
                )

            return self.error_response(
                "Profile not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to refresh session")