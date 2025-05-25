# api/v1/views/accounts.py
"""
Account management ViewSets for API v1
"""

from rest_framework.decorators import action
from rest_framework import status
from datetime import datetime

from .base import BaseModelViewSet
from app.account.models import UserProfile, DoctorProfile
from app.account.serializers import (
    UserProfileSerializer,
    DoctorProfileSerializer,
)
from app.account.permissions import IsProfileOwner, IsDoctorProfile
from app.appointment.models import DoctorAvailability
from app.appointment.serializers import DoctorAvailabilitySerializer
from app.appointment.services import AppointmentService

import logging

logger = logging.getLogger(__name__)


class UserProfileViewSet(BaseModelViewSet):
    """ViewSet for user profiles."""

    serializer_class = UserProfileSerializer

    def get_queryset(self):
        """Filter profiles based on user permissions."""
        user = self.request.user

        if user.is_staff:
            return UserProfile.objects.all()
        else:
            # Users can only see their own profile
            return UserProfile.objects.filter(user=user)

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [IsProfileOwner]
        else:
            permission_classes = [self.permission_classes[0]]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Get current user's profile."""
        try:
            profile = self.get_user_profile()
            if profile:
                return self.success_response(
                    data={"profile": UserProfileSerializer(profile).data}
                )

            return self.error_response(
                "Profile not found", status_code=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to get profile")

    @action(detail=False, methods=["post"])
    def update_profile(self, request):
        """Update current user's profile."""
        try:
            profile = self.get_user_profile()
            if not profile:
                return self.error_response(
                    "Profile not found", status_code=status.HTTP_404_NOT_FOUND
                )

            # Update user fields
            user_data = {
                "first_name": request.data.get("firstName", ""),
                "last_name": request.data.get("lastName", ""),
                "email": request.data.get("email", ""),
            }

            for key, value in user_data.items():
                if value:  # Only update if value provided
                    setattr(request.user, key, value)
            request.user.save()

            # Update profile fields
            profile_data = {
                "phone": request.data.get("phone", ""),
                "address": request.data.get("address", ""),
                "emergency_contact": request.data.get("emergencyContact", ""),
                "emergency_phone": request.data.get("emergencyPhone", ""),
            }

            if profile.role == "patient":
                profile_data["medical_history"] = request.data.get("medicalHistory", "")

            for key, value in profile_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            profile.save()

            return self.success_response(
                data={"profile": UserProfileSerializer(profile).data},
                message="Profile updated successfully",
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to update profile")


class DoctorProfileViewSet(BaseModelViewSet):
    """ViewSet for doctor profiles."""

    serializer_class = DoctorProfileSerializer

    def get_queryset(self):
        """Filter doctor profiles."""
        queryset = DoctorProfile.objects.select_related("user_profile__user")

        # Filter by specialty if provided
        specialty = self.request.query_params.get("specialty")
        if specialty:
            queryset = queryset.filter(specialty__icontains=specialty)

        # Filter by availability
        available_only = self.request.query_params.get("available_only")
        if available_only == "true":
            queryset = queryset.filter(is_available=True, accepts_new_patients=True)

        return queryset

    @action(detail=False, methods=["get"])
    def available_doctors(self, request):
        """Get available doctors for appointment booking."""
        try:
            specialty = request.query_params.get("specialty")

            queryset = DoctorProfile.objects.filter(
                is_available=True, accepts_new_patients=True
            )
            if specialty:
                queryset = queryset.filter(specialty__icontains=specialty)

            doctors = []
            for doctor_profile in queryset.select_related("user_profile__user"):
                doctors.append(
                    {
                        "id": doctor_profile.user_profile.user.id,
                        "name": f"Dr. {doctor_profile.user_profile.user.get_full_name()}",
                        "specialty": doctor_profile.specialty,
                        "rating": float(doctor_profile.rating),
                        "consultation_fee": (
                            float(doctor_profile.consultation_fee)
                            if doctor_profile.consultation_fee
                            else None
                        ),
                        "available": doctor_profile.is_available,
                    }
                )

            return self.success_response(data={"doctors": doctors})

        except Exception as e:
            return self.handle_exception(e, "Failed to get available doctors")

    @action(detail=True, methods=["get"])
    def available_slots(self, request, pk=None):
        """Get available time slots for a doctor."""
        try:
            doctor_profile = self.get_object()
            date_str = request.query_params.get("date")

            if not date_str:
                return self.error_response(
                    "Date parameter is required",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return self.error_response(
                    "Invalid date format. Use YYYY-MM-DD",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            appointment_service = AppointmentService()
            slots = appointment_service.get_available_slots(
                doctor_profile.user_profile.user, date
            )

            return self.success_response(
                data={
                    "date": date_str,
                    "slots": [slot.strftime("%I:%M %p") for slot in slots],
                }
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to get available slots")

    @action(detail=False, methods=["get"])
    def specialties(self, request):
        """Get list of all medical specialties."""
        try:
            specialties = (
                DoctorProfile.objects.values_list("specialty", flat=True)
                .distinct()
                .order_by("specialty")
            )

            return self.success_response(data={"specialties": list(specialties)})

        except Exception as e:
            return self.handle_exception(e, "Failed to get specialties")


class DoctorAvailabilityViewSet(BaseModelViewSet):
    """ViewSet for doctor availability management."""

    serializer_class = DoctorAvailabilitySerializer
    permission_classes = [IsDoctorProfile]

    def get_queryset(self):
        """Get availability for current doctor."""
        try:
            doctor_profile = DoctorProfile.objects.get(
                user_profile__user=self.request.user
            )
            return DoctorAvailability.objects.filter(doctor=doctor_profile)
        except DoctorProfile.DoesNotExist:
            return DoctorAvailability.objects.none()

    def list(self, request):
        """Get doctor's availability with proper response format."""
        try:
            user_profile = self.get_user_profile()
            if not user_profile or user_profile.role != "doctor":
                return self.error_response(
                    "Only doctors can manage availability",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            doctor_profile = user_profile.doctorprofile
            availability = DoctorAvailability.objects.filter(
                doctor=doctor_profile
            ).order_by("day_of_week", "start_time")

            availability_data = []
            for avail in availability:
                availability_data.append(
                    {
                        "id": avail.id,
                        "day_of_week": avail.day_of_week,
                        "start_time": avail.start_time.strftime("%H:%M"),
                        "end_time": avail.end_time.strftime("%H:%M"),
                        "is_available": avail.is_available,
                    }
                )

            return self.success_response(data={"availability": availability_data})

        except Exception as e:
            return self.handle_exception(e, "Failed to get availability")

    def create(self, request):
        """Create new availability slot."""
        try:
            user_profile = self.get_user_profile()
            if not user_profile or user_profile.role != "doctor":
                return self.error_response(
                    "Only doctors can manage availability",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            doctor_profile = user_profile.doctorprofile
            data = request.data

            # Validate required fields
            required_fields = ["day_of_week", "start_time", "end_time"]
            errors = {}
            for field in required_fields:
                if field not in data or not data[field]:
                    errors[field] = f'{field.replace("_", " ").title()} is required'

            if errors:
                return self.error_response(
                    "Validation failed",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    errors=errors,
                )

            # Parse and validate data
            try:
                day_of_week = int(data["day_of_week"])
                start_time = datetime.strptime(data["start_time"], "%H:%M").time()
                end_time = datetime.strptime(data["end_time"], "%H:%M").time()
                is_available = data.get("is_available", True)
            except ValueError as e:
                logger.error(f"Parse error: {e}")
                return self.error_response(
                    "Invalid time format", status_code=status.HTTP_400_BAD_REQUEST
                )

            # Validate day of week
            if day_of_week < 0 or day_of_week > 6:
                return self.error_response(
                    "Invalid day of week", status_code=status.HTTP_400_BAD_REQUEST
                )

            # Validate times
            if start_time >= end_time:
                return self.error_response(
                    "End time must be after start time",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Check for overlapping availability
            overlapping = DoctorAvailability.objects.filter(
                doctor=doctor_profile,
                day_of_week=day_of_week,
                start_time__lt=end_time,
                end_time__gt=start_time,
            )

            if overlapping.exists():
                return self.error_response(
                    "This time slot overlaps with existing availability",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Create availability
            availability = DoctorAvailability.objects.create(
                doctor=doctor_profile,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                is_available=is_available,
            )

            return self.success_response(
                data={
                    "availability": {
                        "id": availability.id,
                        "day_of_week": availability.day_of_week,
                        "start_time": availability.start_time.strftime("%H:%M"),
                        "end_time": availability.end_time.strftime("%H:%M"),
                        "is_available": availability.is_available,
                    }
                },
                message="Availability added successfully",
                status_code=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to create availability")

    def destroy(self, request, pk=None):
        """Delete availability slot."""
        try:
            user_profile = self.get_user_profile()
            doctor_profile = user_profile.doctorprofile

            try:
                availability = DoctorAvailability.objects.get(
                    id=pk, doctor=doctor_profile
                )
                availability.delete()

                return self.success_response(
                    message="Availability deleted successfully"
                )

            except DoctorAvailability.DoesNotExist:
                return self.error_response(
                    "Availability not found", status_code=status.HTTP_404_NOT_FOUND
                )

        except Exception as e:
            return self.handle_exception(e, "Failed to delete availability")

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        """Toggle availability status."""
        try:
            user_profile = self.get_user_profile()
            doctor_profile = user_profile.doctorprofile

            try:
                availability = DoctorAvailability.objects.get(
                    id=pk, doctor=doctor_profile
                )

                # Toggle availability
                availability.is_available = not availability.is_available
                availability.save()

                status_text = "enabled" if availability.is_available else "disabled"

                return self.success_response(
                    data={"is_available": availability.is_available},
                    message=f"Availability {status_text} successfully",
                )

            except DoctorAvailability.DoesNotExist:
                return self.error_response(
                    "Availability not found", status_code=status.HTTP_404_NOT_FOUND
                )

        except Exception as e:
            return self.handle_exception(e, "Failed to toggle availability")
