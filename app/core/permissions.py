"""
Custom permissions for the CareBridge application.
"""

from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.throttling import UserRateThrottle


class IsPatient(IsAuthenticated):
    """Permission class for patient users."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return (
            hasattr(request.user, "userprofile")
            and request.user.userprofile.role == "patient"
        )


class IsDoctor(IsAuthenticated):
    """Permission class for doctor users."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return (
            hasattr(request.user, "userprofile")
            and request.user.userprofile.role == "doctor"
        )


class IsAdmin(IsAuthenticated):
    """Permission class for admin users."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return (
            hasattr(request.user, "userprofile")
            and request.user.userprofile.role == "admin"
        )


class IsDoctorOrPatient(IsAuthenticated):
    """Permission class for both doctor and patient users."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if not hasattr(request.user, "userprofile"):
            return False
        return request.user.userprofile.role in ["doctor", "patient"]


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        # Write permissions are only allowed to the owner of the object
        return obj.user == request.user


class AppointmentBookingThrottle(UserRateThrottle):
    """Custom throttle for appointment booking."""

    scope = "appointment_booking"
    rate = "10/min"
