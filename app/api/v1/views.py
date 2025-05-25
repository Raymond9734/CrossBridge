# api/v1/views.py - Comprehensive API views for SPA
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from django.db.models import Count, Avg

import logging

import csv
from io import StringIO

# Import services
from app.account.services import DoctorProfileService
from app.appointment.services import AppointmentService
from app.medical_record.services import (
    MedicalRecordService,
    PrescriptionService,
    ReviewService,
)
from app.notification.services import NotificationService

# Import serializers
from app.account.serializers import (
    UserProfileSerializer,
    DoctorProfileSerializer,
    UserRegistrationSerializer,
)
from app.appointment.serializers import (
    AppointmentBookingSerializer,
    AppointmentSerializer,
    DoctorAvailabilitySerializer,
)
from app.medical_record.serializers import (
    MedicalRecordSerializer,
    PrescriptionSerializer,
    LabResultSerializer,
    ReviewSerializer,
)
from app.notification.serializers import (
    NotificationSerializer,
    NotificationPreferenceSerializer,
)

# Import models
from app.account.models import UserProfile, DoctorProfile
from app.appointment.models import Appointment, DoctorAvailability
from app.medical_record.models import MedicalRecord, Prescription, LabResult, Review
from app.notification.models import Notification, NotificationPreference

# Import permissions
from app.core.permissions import (
    AppointmentBookingThrottle,
    IsPatient,
    IsDoctor,
    IsDoctorOrPatient,
)
from app.account.permissions import IsProfileOwner, IsDoctorProfile

logger = logging.getLogger(__name__)


class AuthViewSet(viewsets.ViewSet):
    """Authentication endpoints."""

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @action(detail=False, methods=["post"])
    def login(self, request):
        """Login endpoint."""
        email = request.data.get("email")
        password = request.data.get("password")
        remember = request.data.get("remember", False)

        if not email or not password:
            return Response(
                {"success": False, "error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
        except User.DoesNotExist:
            return Response(
                {"success": False, "error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
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

            return Response(
                {"success": True, "message": "Login successful", "user": profile_data}
            )

        return Response(
            {"success": False, "error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    @action(detail=False, methods=["post"])
    def register(self, request):
        """Registration endpoint."""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)

            # Get created profile
            profile = UserProfile.objects.get(user=user)
            profile_data = UserProfileSerializer(profile).data

            return Response(
                {
                    "success": True,
                    "message": "Registration successful",
                    "user": profile_data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=["post"])
    def logout(self, request):
        """Logout endpoint."""
        logout(request)
        return Response({"success": True, "message": "Logout successful"})

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Get current user profile."""
        if request.user.is_authenticated:
            try:
                profile = UserProfile.objects.get(user=request.user)
                return Response(
                    {"success": True, "user": UserProfileSerializer(profile).data}
                )
            except UserProfile.DoesNotExist:
                return Response(
                    {"success": False, "error": "Profile not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        return Response(
            {"success": False, "error": "Not authenticated"},
            status=status.HTTP_401_UNAUTHORIZED,
        )


class DashboardViewSet(viewsets.ViewSet):
    """Dashboard data endpoints."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def data(self, request):
        """Get dashboard data based on user role."""
        try:
            user_profile = UserProfile.objects.get(user=request.user)

            if user_profile.role == "doctor":
                dashboard_data = self._get_doctor_dashboard_data(request.user)
            else:
                dashboard_data = self._get_patient_dashboard_data(request.user)

            # Get notifications
            notification_service = NotificationService()
            notifications = notification_service.get_user_notifications(
                request.user, unread_only=True, limit=10
            )

            notifications_data = {
                "unread_count": len(notifications),
                "items": [
                    {
                        "id": notif.id,
                        "type": notif.notification_type,
                        "title": notif.title,
                        "message": notif.message,
                        "created_at": notif.created_at.isoformat(),
                    }
                    for notif in notifications
                ],
            }

            dashboard_data.update(
                {
                    "user": {
                        "id": request.user.id,
                        "name": request.user.get_full_name(),
                        "email": request.user.email,
                        "role": user_profile.role,
                    },
                    "notifications": notifications_data,
                }
            )

            return Response({"success": True, "data": dashboard_data})

        except Exception as e:
            logger.error(f"Dashboard error for user {request.user.id}: {e}")
            return Response(
                {"success": False, "error": "Unable to load dashboard data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_patient_dashboard_data(self, user):
        """Get dashboard data for patients"""
        appointment_service = AppointmentService()
        medical_record_service = MedicalRecordService()

        # Get upcoming appointments
        upcoming_appointments = appointment_service.get_patient_appointments(
            user, status="confirmed"
        )[:5]

        # Get recent medical records
        recent_records = medical_record_service.get_patient_records(user, limit=5)

        # Format appointments
        appointments_data = []
        for apt in upcoming_appointments:
            appointments_data.append(
                {
                    "id": apt.id,
                    "doctor": f"Dr. {apt.doctor.get_full_name()}",
                    "type": apt.get_appointment_type_display(),
                    "date": apt.appointment_date.strftime("%Y-%m-%d"),
                    "time": apt.start_time.strftime("%I:%M %p"),
                    "status": apt.status,
                }
            )

        # Format medical records
        records_data = []
        for record in recent_records:
            records_data.append(
                {
                    "id": record.id,
                    "title": (
                        record.diagnosis[:50] + "..."
                        if record.diagnosis and len(record.diagnosis) > 50
                        else record.diagnosis or "General Consultation"
                    ),
                    "doctor": f"Dr. {record.doctor.get_full_name()}",
                    "date": record.created_at.strftime("%B %d, %Y"),
                }
            )

        # Get statistics
        total_appointments = Appointment.objects.filter(patient=user).count()
        completed_appointments = Appointment.objects.filter(
            patient=user, status="completed"
        ).count()

        return {
            "stats": {
                "upcoming_appointments": len(upcoming_appointments),
                "completed_visits": completed_appointments,
                "total_appointments": total_appointments,
            },
            "appointments": appointments_data,
            "medical_records": records_data,
        }

    def _get_doctor_dashboard_data(self, user):
        """Get dashboard data for doctors"""
        appointment_service = AppointmentService()
        doctor_service = DoctorProfileService()
        today = timezone.now().date()

        # Get today's appointments
        todays_appointments = appointment_service.get_doctor_appointments(
            user, date=today
        )

        # Format appointments
        appointments_data = []
        for apt in todays_appointments:
            appointments_data.append(
                {
                    "id": apt.id,
                    "patient": apt.patient.get_full_name(),
                    "type": apt.get_appointment_type_display(),
                    "time": apt.start_time.strftime("%I:%M %p"),
                    "status": apt.status,
                }
            )

        # Get statistics
        stats = doctor_service.get_patient_statistics(user)

        return {
            "stats": {
                "todays_appointments": len(todays_appointments),
                "total_patients": stats.get("total_patients", 0),
                "pending_reviews": stats.get("pending_reviews", 0),
            },
            "appointments": appointments_data,
            "patients": [],  # Will be loaded separately via patients endpoint
        }


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for user profiles."""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

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
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Get current user's profile."""
        try:
            profile = UserProfile.objects.get(user=request.user)
            return Response(
                {"success": True, "profile": UserProfileSerializer(profile).data}
            )
        except UserProfile.DoesNotExist:
            return Response(
                {"success": False, "error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["post"])
    def update_profile(self, request):
        """Update current user's profile."""
        try:
            profile = UserProfile.objects.get(user=request.user)

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

            return Response(
                {
                    "success": True,
                    "message": "Profile updated successfully",
                    "profile": UserProfileSerializer(profile).data,
                }
            )

        except UserProfile.DoesNotExist:
            return Response(
                {"success": False, "error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Profile update error: {e}")
            return Response(
                {"success": False, "error": "Failed to update profile"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DoctorProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for doctor profiles."""

    serializer_class = DoctorProfileSerializer
    permission_classes = [IsAuthenticated]

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

            return Response({"success": True, "doctors": doctors})
        except Exception as e:
            logger.error(f"Error fetching available doctors: {e}")
            return Response({"success": False, "doctors": []})

    @action(detail=True, methods=["get"])
    def available_slots(self, request, pk=None):
        """Get available time slots for a doctor."""
        try:
            doctor_profile = self.get_object()
            date_str = request.query_params.get("date")

            if not date_str:
                return Response(
                    {"success": False, "error": "Date parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"success": False, "error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            appointment_service = AppointmentService()
            slots = appointment_service.get_available_slots(
                doctor_profile.user_profile.user, date
            )

            return Response(
                {
                    "success": True,
                    "date": date_str,
                    "slots": [slot.strftime("%I:%M %p") for slot in slots],
                }
            )
        except Exception as e:
            logger.error(f"Error fetching available slots: {e}")
            return Response({"success": False, "slots": []})


# Add more comprehensive API endpoints for all other functionality...
# (Continue with remaining ViewSets for appointments, medical records, etc.)


class AppointmentViewSet(viewsets.ModelViewSet):
    """ViewSet for appointments."""

    serializer_class = AppointmentSerializer
    permission_classes = [IsDoctorOrPatient]

    def get_queryset(self):
        """Filter appointments based on user role."""
        user = self.request.user

        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role == "doctor":
                queryset = Appointment.objects.filter(doctor=user)
            else:
                queryset = Appointment.objects.filter(patient=user)
        except UserProfile.DoesNotExist:
            return Appointment.objects.none()

        # Apply filters
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        date_from = self.request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(appointment_date__gte=date_from)

        date_to = self.request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(appointment_date__lte=date_to)

        return queryset.select_related("patient", "doctor")

    def list(self, request):
        """List appointments with proper response format."""
        try:
            queryset = self.get_queryset()

            appointments_data = []
            for apt in queryset[:50]:  # Limit to 50 most recent
                appointments_data.append(
                    {
                        "id": apt.id,
                        "patient": apt.patient.get_full_name(),
                        "doctor": f"Dr. {apt.doctor.get_full_name()}",
                        "date": apt.appointment_date.strftime("%Y-%m-%d"),
                        "time": apt.start_time.strftime("%I:%M %p"),
                        "type": apt.get_appointment_type_display(),
                        "status": apt.status,
                    }
                )

            return Response({"success": True, "appointments": appointments_data})

        except Exception as e:
            logger.error(f"Error fetching appointments: {e}")
            return Response(
                {
                    "success": False,
                    "appointments": [],
                    "error": "Unable to load appointments",
                }
            )

    @action(detail=False, methods=["post"])
    def book(self, request):
        """Book a new appointment."""
        try:
            appointment_service = AppointmentService()

            doctor_name = request.data.get("doctor")
            appointment_date = request.data.get("date")
            appointment_time = request.data.get("time")
            appointment_type = request.data.get("type")
            notes = request.data.get("notes", "")

            # Find doctor
            try:
                # Extract name from "Dr. FirstName LastName" format
                name_parts = doctor_name.replace("Dr. ", "").split()
                if len(name_parts) >= 2:
                    first_name, last_name = name_parts[0], name_parts[1]
                    doctor_user = User.objects.get(
                        first_name__icontains=first_name,
                        last_name__icontains=last_name,
                        userprofile__role="doctor",
                    )
                else:
                    return Response(
                        {"success": False, "error": "Invalid doctor name format"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except User.DoesNotExist:
                return Response(
                    {"success": False, "error": "Doctor not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Parse date and time
            try:
                apt_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
                apt_time = datetime.strptime(appointment_time, "%I:%M %p").time()
            except ValueError:
                return Response(
                    {"success": False, "error": "Invalid date or time format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Map frontend types to model choices
            type_mapping = {
                "Consultation": "consultation",
                "Follow-up": "follow_up",
                "Checkup": "checkup",
                "Emergency": "emergency",
            }

            # Book appointment using service
            appointment = appointment_service.book_appointment(
                patient=request.user,
                doctor_id=doctor_user.id,
                appointment_date=apt_date,
                start_time=apt_time,
                appointment_type=type_mapping.get(appointment_type, "consultation"),
                patient_notes=notes,
            )

            return Response(
                {
                    "success": True,
                    "message": "Appointment booked successfully!",
                    "appointment": AppointmentSerializer(appointment).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Appointment booking error: {e}")
            return Response(
                {"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """Confirm an appointment (doctor only)."""
        try:
            appointment = self.get_object()

            # Only doctor can confirm
            if request.user != appointment.doctor:
                return Response(
                    {
                        "success": False,
                        "error": "Only the doctor can confirm appointments",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            appointment_service = AppointmentService()
            appointment_service.confirm_appointment(appointment)

            return Response(
                {"success": True, "message": "Appointment confirmed successfully"}
            )
        except Exception as e:
            logger.error(f"Appointment confirmation error: {e}")
            return Response(
                {"success": False, "error": "Failed to confirm appointment"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel an appointment."""
        try:
            appointment = self.get_object()
            reason = request.data.get("reason", "")

            # Check if user can cancel this appointment
            if request.user not in [appointment.patient, appointment.doctor]:
                return Response(
                    {"success": False, "error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            appointment_service = AppointmentService()
            appointment_service.cancel_appointment(appointment, request.user, reason)

            return Response(
                {"success": True, "message": "Appointment cancelled successfully"}
            )
        except Exception as e:
            logger.error(f"Appointment cancellation error: {e}")
            return Response(
                {"success": False, "error": "Failed to cancel appointment"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DoctorAvailabilityViewSet(viewsets.ModelViewSet):
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
            user_profile = request.user.userprofile
            if user_profile.role != "doctor":
                return Response(
                    {"success": False, "error": "Only doctors can manage availability"},
                    status=status.HTTP_403_FORBIDDEN,
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

            return Response({"success": True, "availability": availability_data})

        except Exception as e:
            logger.error(f"Error getting doctor availability: {e}")
            return Response(
                {"success": False, "error": "Doctor profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def create(self, request):
        """Create new availability slot."""
        try:
            user_profile = request.user.userprofile
            if user_profile.role != "doctor":
                return Response(
                    {"success": False, "error": "Only doctors can manage availability"},
                    status=status.HTTP_403_FORBIDDEN,
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
                return Response(
                    {"success": False, "errors": errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Parse and validate data
            try:
                day_of_week = int(data["day_of_week"])
                start_time = datetime.strptime(data["start_time"], "%H:%M").time()
                end_time = datetime.strptime(data["end_time"], "%H:%M").time()
                is_available = data.get("is_available", True)
            except ValueError as e:
                logger.error(f" {e}")
                return Response(
                    {"success": False, "errors": {"general": "Invalid time format"}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate day of week
            if day_of_week < 0 or day_of_week > 6:
                return Response(
                    {
                        "success": False,
                        "errors": {"day_of_week": "Invalid day of week"},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate times
            if start_time >= end_time:
                return Response(
                    {
                        "success": False,
                        "errors": {"end_time": "End time must be after start time"},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check for overlapping availability
            overlapping = DoctorAvailability.objects.filter(
                doctor=doctor_profile,
                day_of_week=day_of_week,
                start_time__lt=end_time,
                end_time__gt=start_time,
            )

            if overlapping.exists():
                return Response(
                    {
                        "success": False,
                        "errors": {
                            "general": "This time slot overlaps with existing availability"
                        },
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create availability
            availability = DoctorAvailability.objects.create(
                doctor=doctor_profile,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                is_available=is_available,
            )

            return Response(
                {
                    "success": True,
                    "message": "Availability added successfully",
                    "availability": {
                        "id": availability.id,
                        "day_of_week": availability.day_of_week,
                        "start_time": availability.start_time.strftime("%H:%M"),
                        "end_time": availability.end_time.strftime("%H:%M"),
                        "is_available": availability.is_available,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error creating availability: {e}")
            return Response(
                {
                    "success": False,
                    "errors": {"general": "Failed to create availability"},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def destroy(self, request, pk=None):
        """Delete availability slot."""
        try:
            user_profile = request.user.userprofile
            doctor_profile = user_profile.doctorprofile

            try:
                availability = DoctorAvailability.objects.get(
                    id=pk, doctor=doctor_profile
                )
                availability.delete()

                return Response(
                    {"success": True, "message": "Availability deleted successfully"}
                )

            except DoctorAvailability.DoesNotExist:
                return Response(
                    {"success": False, "error": "Availability not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        except Exception as e:
            logger.error(f"Error deleting availability: {e}")
            return Response(
                {"success": False, "error": "Failed to delete availability"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        """Toggle availability status."""
        try:
            user_profile = request.user.userprofile
            doctor_profile = user_profile.doctorprofile

            try:
                availability = DoctorAvailability.objects.get(
                    id=pk, doctor=doctor_profile
                )

                # Toggle availability
                availability.is_available = not availability.is_available
                availability.save()

                status_text = "enabled" if availability.is_available else "disabled"

                return Response(
                    {
                        "success": True,
                        "message": f"Availability {status_text} successfully",
                        "is_available": availability.is_available,
                    }
                )

            except DoctorAvailability.DoesNotExist:
                return Response(
                    {"success": False, "error": "Availability not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        except Exception as e:
            logger.error(f"Error toggling availability: {e}")
            return Response(
                {"success": False, "error": "Failed to toggle availability"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MedicalRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for medical records."""

    serializer_class = MedicalRecordSerializer
    permission_classes = [IsDoctorOrPatient]

    def get_queryset(self):
        """Filter medical records based on user role."""
        user = self.request.user

        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role == "doctor":
                return MedicalRecord.objects.filter(appointment__doctor=user)
            else:
                return MedicalRecord.objects.filter(appointment__patient=user)
        except UserProfile.DoesNotExist:
            return MedicalRecord.objects.none()

    def list(self, request):
        """List medical records with proper response format."""
        try:
            user_profile = UserProfile.objects.get(user=request.user)

            if user_profile.role == "doctor":
                records = (
                    MedicalRecord.objects.filter(appointment__doctor=request.user)
                    .select_related("appointment", "appointment__patient")
                    .prefetch_related("prescriptions", "lab_results_records")[:50]
                )
            else:
                records = (
                    MedicalRecord.objects.filter(appointment__patient=request.user)
                    .select_related("appointment", "appointment__doctor")
                    .prefetch_related("prescriptions", "lab_results_records")[:50]
                )

            records_data = []
            for record in records:
                records_data.append(
                    {
                        "id": record.id,
                        "appointment_id": record.appointment.id,
                        "patient_name": record.patient.get_full_name(),
                        "doctor_name": f"Dr. {record.doctor.get_full_name()}",
                        "appointment_date": record.appointment.appointment_date.strftime(
                            "%Y-%m-%d"
                        ),
                        "appointment_type": record.appointment.get_appointment_type_display(),
                        "diagnosis": record.diagnosis,
                        "treatment": record.treatment,
                        "prescription": record.prescription,
                        "follow_up_required": record.follow_up_required,
                        "follow_up_date": (
                            record.follow_up_date.strftime("%Y-%m-%d")
                            if record.follow_up_date
                            else None
                        ),
                        "blood_pressure": record.blood_pressure,
                        "heart_rate": record.heart_rate,
                        "temperature": (
                            str(record.temperature) if record.temperature else None
                        ),
                        "weight": str(record.weight) if record.weight else None,
                        "height": str(record.height) if record.height else None,
                        "bmi": record.bmi,
                        "created_at": record.created_at.isoformat(),
                    }
                )

            return Response({"success": True, "medical_records": records_data})

        except UserProfile.DoesNotExist:
            return Response(
                {"success": False, "error": "User profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error fetching medical records: {e}")
            return Response(
                {
                    "success": False,
                    "medical_records": [],
                    "error": "Unable to load medical records",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ["create", "update", "partial_update"]:
            # Only doctors can create/update medical records
            permission_classes = [IsDoctor]
        else:
            permission_classes = [IsDoctorOrPatient]

        return [permission() for permission in permission_classes]

    def create(self, request):
        """Create medical record (doctor only)."""
        try:
            # Verify user is a doctor
            user_profile = UserProfile.objects.get(user=request.user)
            if user_profile.role != "doctor":
                return Response(
                    {
                        "success": False,
                        "error": "Only doctors can create medical records",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            appointment_id = request.data.get("appointment_id")
            if not appointment_id:
                return Response(
                    {"success": False, "error": "Appointment ID is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                appointment = Appointment.objects.get(
                    id=appointment_id, doctor=request.user
                )
            except Appointment.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "error": "Appointment not found or access denied",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Check if medical record already exists
            if hasattr(appointment, "medical_record"):
                return Response(
                    {
                        "success": False,
                        "error": "Medical record already exists for this appointment",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Extract vitals and other data
            vitals_data = {
                "blood_pressure_systolic": request.data.get("blood_pressure_systolic"),
                "blood_pressure_diastolic": request.data.get(
                    "blood_pressure_diastolic"
                ),
                "heart_rate": request.data.get("heart_rate"),
                "temperature": request.data.get("temperature"),
                "weight": request.data.get("weight"),
                "height": request.data.get("height"),
            }

            medical_record_service = MedicalRecordService()
            record = medical_record_service.create_record(
                appointment=appointment,
                diagnosis=request.data.get("diagnosis", ""),
                treatment=request.data.get("treatment", ""),
                vitals=vitals_data,
            )

            # Additional fields
            record.prescription = request.data.get("prescription", "")
            record.lab_results = request.data.get("lab_results", "")
            record.allergies = request.data.get("allergies", "")
            record.medications = request.data.get("medications", "")
            record.medical_history = request.data.get("medical_history", "")
            record.follow_up_required = request.data.get("follow_up_required", False)

            if record.follow_up_required and request.data.get("follow_up_date"):
                record.follow_up_date = datetime.strptime(
                    request.data.get("follow_up_date"), "%Y-%m-%d"
                ).date()

            record.save()

            return Response(
                {
                    "success": True,
                    "message": "Medical record created successfully",
                    "medical_record": MedicalRecordSerializer(record).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error creating medical record: {e}")
            return Response(
                {"success": False, "error": "Failed to create medical record"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PrescriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for prescriptions."""

    serializer_class = PrescriptionSerializer
    permission_classes = [IsDoctorOrPatient]

    def get_queryset(self):
        """Filter prescriptions based on user role."""
        user = self.request.user

        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role == "doctor":
                return Prescription.objects.filter(
                    medical_record__appointment__doctor=user
                )
            else:
                return Prescription.objects.filter(
                    medical_record__appointment__patient=user
                )
        except UserProfile.DoesNotExist:
            return Prescription.objects.none()

    def list(self, request):
        """List prescriptions with proper response format."""
        try:
            queryset = self.get_queryset()

            # Filter by active status if requested
            active_only = request.query_params.get("active_only")
            if active_only == "true":
                queryset = queryset.filter(is_active=True)

            prescriptions_data = []
            for prescription in queryset.select_related(
                "medical_record__appointment__patient",
                "medical_record__appointment__doctor",
            )[:50]:
                prescriptions_data.append(
                    {
                        "id": prescription.id,
                        "medication_name": prescription.medication_name,
                        "dosage": prescription.dosage,
                        "frequency": prescription.frequency,
                        "duration": prescription.duration,
                        "instructions": prescription.instructions,
                        "quantity": prescription.quantity,
                        "refills": prescription.refills,
                        "is_generic_allowed": prescription.is_generic_allowed,
                        "is_active": prescription.is_active,
                        "date_prescribed": prescription.date_prescribed.strftime(
                            "%Y-%m-%d"
                        ),
                        "date_filled": (
                            prescription.date_filled.strftime("%Y-%m-%d")
                            if prescription.date_filled
                            else None
                        ),
                        "patient_name": prescription.patient.get_full_name(),
                        "doctor_name": f"Dr. {prescription.doctor.get_full_name()}",
                    }
                )

            return Response({"success": True, "prescriptions": prescriptions_data})

        except Exception as e:
            logger.error(f"Error fetching prescriptions: {e}")
            return Response(
                {
                    "success": False,
                    "prescriptions": [],
                    "error": "Unable to load prescriptions",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_permissions(self):
        """Only doctors can create/update prescriptions."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsDoctor]
        else:
            permission_classes = [IsDoctorOrPatient]

        return [permission() for permission in permission_classes]

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """Deactivate a prescription."""
        try:
            prescription = self.get_object()

            # Only prescribing doctor can deactivate
            if request.user != prescription.medical_record.appointment.doctor:
                return Response(
                    {"success": False, "error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            prescription_service = PrescriptionService()
            prescription_service.deactivate_prescription(prescription)

            return Response(
                {"success": True, "message": "Prescription deactivated successfully"}
            )

        except Exception as e:
            logger.error(f"Error deactivating prescription: {e}")
            return Response(
                {"success": False, "error": "Failed to deactivate prescription"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LabResultViewSet(viewsets.ModelViewSet):
    """ViewSet for lab results."""

    serializer_class = LabResultSerializer
    permission_classes = [IsDoctorOrPatient]

    def get_queryset(self):
        """Filter lab results based on user role."""
        user = self.request.user

        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role == "doctor":
                return LabResult.objects.filter(
                    medical_record__appointment__doctor=user
                )
            else:
                return LabResult.objects.filter(
                    medical_record__appointment__patient=user
                )
        except UserProfile.DoesNotExist:
            return LabResult.objects.none()

    def list(self, request):
        """List lab results with proper response format."""
        try:
            queryset = self.get_queryset()

            # Filter by test type if requested
            test_type = request.query_params.get("test_type")
            if test_type:
                queryset = queryset.filter(test_type=test_type)

            lab_results_data = []
            for result in queryset.select_related(
                "medical_record__appointment__patient",
                "medical_record__appointment__doctor",
            )[:50]:
                lab_results_data.append(
                    {
                        "id": result.id,
                        "test_name": result.test_name,
                        "test_type": result.get_test_type_display(),
                        "result_value": result.result_value,
                        "result_unit": result.result_unit,
                        "reference_range": result.reference_range,
                        "status": result.get_status_display(),
                        "notes": result.notes,
                        "ordered_date": result.ordered_date.strftime("%Y-%m-%d"),
                        "result_date": (
                            result.result_date.strftime("%Y-%m-%d")
                            if result.result_date
                            else None
                        ),
                        "is_abnormal": result.is_abnormal,
                        "patient_name": result.medical_record.patient.get_full_name(),
                    }
                )

            return Response({"success": True, "lab_results": lab_results_data})

        except Exception as e:
            logger.error(f"Error fetching lab results: {e}")
            return Response(
                {
                    "success": False,
                    "lab_results": [],
                    "error": "Unable to load lab results",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_permissions(self):
        """Only doctors can create/update lab results."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsDoctor]
        else:
            permission_classes = [IsDoctorOrPatient]

        return [permission() for permission in permission_classes]


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for reviews."""

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter reviews based on user role."""
        user = self.request.user

        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role == "doctor":
                return Review.objects.filter(doctor=user)
            else:
                return Review.objects.filter(patient=user)
        except UserProfile.DoesNotExist:
            return Review.objects.none()

    def list(self, request):
        """List reviews with proper response format."""
        try:
            queryset = self.get_queryset()

            # Filter by doctor if requested (for public viewing)
            doctor_id = request.query_params.get("doctor_id")
            if doctor_id:
                queryset = Review.objects.filter(doctor_id=doctor_id, is_verified=True)

            reviews_data = []
            for review in queryset.select_related("patient", "doctor", "appointment")[
                :50
            ]:
                reviews_data.append(
                    {
                        "id": review.id,
                        "rating": review.rating,
                        "review_text": review.review_text,
                        "communication_rating": review.communication_rating,
                        "professionalism_rating": review.professionalism_rating,
                        "wait_time_rating": review.wait_time_rating,
                        "is_verified": review.is_verified,
                        "is_anonymous": review.is_anonymous,
                        "patient_name": (
                            "Anonymous"
                            if review.is_anonymous
                            else review.patient.get_full_name()
                        ),
                        "doctor_name": f"Dr. {review.doctor.get_full_name()}",
                        "created_at": review.created_at.strftime("%Y-%m-%d"),
                    }
                )

            return Response({"success": True, "reviews": reviews_data})

        except Exception as e:
            logger.error(f"Error fetching reviews: {e}")
            return Response(
                {"success": False, "reviews": [], "error": "Unable to load reviews"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_permissions(self):
        """Only patients can create reviews."""
        if self.action in ["create"]:
            permission_classes = [IsPatient]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def create(self, request):
        """Create review (patient only)."""
        try:
            review_service = ReviewService()

            doctor_id = request.data.get("doctor_id")
            appointment_id = request.data.get("appointment_id")
            rating = request.data.get("rating")

            if not all([doctor_id, rating]):
                return Response(
                    {"success": False, "error": "Doctor ID and rating are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                doctor = User.objects.get(id=doctor_id, userprofile__role="doctor")
            except User.DoesNotExist:
                return Response(
                    {"success": False, "error": "Doctor not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            appointment = None
            if appointment_id:
                try:
                    appointment = Appointment.objects.get(
                        id=appointment_id,
                        patient=request.user,
                        doctor=doctor,
                        status="completed",
                    )
                except Appointment.DoesNotExist:
                    return Response(
                        {"success": False, "error": "Completed appointment not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            detailed_ratings = {
                "communication_rating": request.data.get("communication_rating"),
                "professionalism_rating": request.data.get("professionalism_rating"),
                "wait_time_rating": request.data.get("wait_time_rating"),
            }

            review = review_service.create_review(
                patient=request.user,
                doctor=doctor,
                appointment=appointment,
                rating=int(rating),
                review_text=request.data.get("review_text", ""),
                detailed_ratings=detailed_ratings,
            )

            return Response(
                {
                    "success": True,
                    "message": "Review created successfully",
                    "review": ReviewSerializer(review).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error creating review: {e}")
            return Response(
                {"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for notifications."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get notifications for current user."""
        queryset = Notification.objects.filter(user=self.request.user)

        # Filter by read status
        unread_only = self.request.query_params.get("unread_only")
        if unread_only == "true":
            queryset = queryset.filter(is_read=False)

        return queryset.select_related("appointment")

    def list(self, request):
        """List notifications with proper response format."""
        try:
            queryset = self.get_queryset()

            notifications_data = []
            for notification in queryset[:50]:
                notifications_data.append(
                    {
                        "id": notification.id,
                        "type": notification.notification_type,
                        "priority": notification.priority,
                        "title": notification.title,
                        "message": notification.message,
                        "is_read": notification.is_read,
                        "read_at": (
                            notification.read_at.isoformat()
                            if notification.read_at
                            else None
                        ),
                        "created_at": notification.created_at.isoformat(),
                        "appointment_id": (
                            notification.appointment.id
                            if notification.appointment
                            else None
                        ),
                    }
                )

            return Response(
                {
                    "success": True,
                    "notifications": notifications_data,
                    "unread_count": queryset.filter(is_read=False).count(),
                }
            )

        except Exception as e:
            logger.error(f"Error fetching notifications: {e}")
            return Response(
                {
                    "success": False,
                    "notifications": [],
                    "error": "Unable to load notifications",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_permissions(self):
        """Users can only view/update their own notifications."""
        if self.action in ["create", "destroy"]:
            # Only system can create/delete notifications
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        try:
            notification_service = NotificationService()

            notification_ids = request.data.get("notification_ids", [])
            if not notification_ids:
                # Mark all unread notifications as read
                notification_ids = list(
                    Notification.objects.filter(
                        user=request.user, is_read=False
                    ).values_list("id", flat=True)
                )

            count = notification_service.mark_as_read(notification_ids, request.user)

            return Response(
                {
                    "success": True,
                    "message": f"Marked {count} notifications as read",
                    "count": count,
                }
            )

        except Exception as e:
            logger.error(f"Error marking notifications as read: {e}")
            return Response(
                {"success": False, "error": "Failed to mark notifications as read"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        """Mark specific notification as read."""
        try:
            notification = self.get_object()
            notification.mark_as_read()

            return Response({"success": True, "message": "Notification marked as read"})

        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return Response(
                {"success": False, "error": "Failed to mark notification as read"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """ViewSet for notification preferences."""

    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get preferences for current user."""
        return NotificationPreference.objects.filter(user=self.request.user)

    def get_object(self):
        """Get or create preferences for current user."""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preferences

    def list(self, request):
        """Get current user's notification preferences."""
        try:
            preferences = self.get_object()
            return Response(
                {
                    "success": True,
                    "preferences": NotificationPreferenceSerializer(preferences).data,
                }
            )
        except Exception as e:
            logger.error(f"Error fetching notification preferences: {e}")
            return Response(
                {"success": False, "error": "Failed to load preferences"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def update(self, request, pk=None):
        """Update notification preferences."""
        try:
            preferences = self.get_object()
            serializer = self.get_serializer(
                preferences, data=request.data, partial=True
            )

            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "success": True,
                        "message": "Preferences updated successfully",
                        "preferences": serializer.data,
                    }
                )

            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.error(f"Error updating notification preferences: {e}")
            return Response(
                {"success": False, "error": "Failed to update preferences"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PatientManagementViewSet(viewsets.ViewSet):
    """ViewSet for doctor patient management."""

    permission_classes = [IsDoctor]

    @action(detail=False, methods=["get"])
    def patients(self, request):  # Changed from 'list' to 'patients'
        """Get patients for current doctor."""
        try:
            # Get patients who have appointments with this doctor
            patients_query = (
                Appointment.objects.filter(doctor=request.user)
                .values("patient")
                .distinct()
            )

            patients_data = []
            for patient_data in patients_query:
                try:
                    patient = User.objects.get(id=patient_data["patient"])
                    patient_profile = patient.userprofile

                    # Get appointment stats
                    total_appointments = Appointment.objects.filter(
                        doctor=request.user, patient=patient
                    ).count()

                    last_appointment = (
                        Appointment.objects.filter(doctor=request.user, patient=patient)
                        .order_by("-appointment_date")
                        .first()
                    )

                    patients_data.append(
                        {
                            "id": patient.id,
                            "name": patient.get_full_name(),
                            "email": patient.email,
                            "phone": patient_profile.phone,
                            "date_of_birth": (
                                patient_profile.date_of_birth.strftime("%Y-%m-%d")
                                if patient_profile.date_of_birth
                                else None
                            ),
                            "gender": (
                                patient_profile.get_gender_display()
                                if patient_profile.gender
                                else None
                            ),
                            "address": patient_profile.address,
                            "emergency_contact": patient_profile.emergency_contact,
                            "emergency_phone": patient_profile.emergency_phone,
                            "medical_history": patient_profile.medical_history,
                            "insurance_info": patient_profile.insurance_info,
                            "total_appointments": total_appointments,
                            "last_visit": (
                                last_appointment.appointment_date.strftime("%Y-%m-%d")
                                if last_appointment
                                else None
                            ),
                            "created_at": patient_profile.created_at.isoformat(),
                        }
                    )
                except User.DoesNotExist:
                    continue

            return Response({"success": True, "patients": patients_data})

        except Exception as e:
            logger.error(f"Error fetching patients: {e}")
            return Response(
                {"success": False, "patients": [], "error": "Unable to load patients"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def detail(self, request, pk=None):
        """Get detailed patient information."""
        try:
            patient = User.objects.get(id=pk)

            # Verify this doctor has treated this patient
            if not Appointment.objects.filter(
                doctor=request.user, patient=patient
            ).exists():
                return Response(
                    {"success": False, "error": "Patient not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            patient_profile = patient.userprofile

            # Get recent appointments
            recent_appointments = Appointment.objects.filter(
                doctor=request.user, patient=patient
            ).order_by("-appointment_date")[:10]

            appointments_data = []
            for apt in recent_appointments:
                appointments_data.append(
                    {
                        "id": apt.id,
                        "date": apt.appointment_date.strftime("%Y-%m-%d"),
                        "time": apt.start_time.strftime("%I:%M %p"),
                        "type": apt.get_appointment_type_display(),
                        "status": apt.status,
                    }
                )

            # Get medical records
            medical_records = MedicalRecord.objects.filter(
                appointment__doctor=request.user, appointment__patient=patient
            ).order_by("-created_at")[:10]

            records_data = []
            for record in medical_records:
                records_data.append(
                    {
                        "id": record.id,
                        "date": record.created_at.strftime("%Y-%m-%d"),
                        "diagnosis": record.diagnosis,
                        "treatment": record.treatment,
                        "appointment_type": record.appointment.get_appointment_type_display(),
                    }
                )

            patient_detail = {
                "id": patient.id,
                "name": patient.get_full_name(),
                "email": patient.email,
                "phone": patient_profile.phone,
                "date_of_birth": (
                    patient_profile.date_of_birth.strftime("%Y-%m-%d")
                    if patient_profile.date_of_birth
                    else None
                ),
                "gender": (
                    patient_profile.get_gender_display()
                    if patient_profile.gender
                    else None
                ),
                "address": patient_profile.address,
                "emergency_contact": patient_profile.emergency_contact,
                "emergency_phone": patient_profile.emergency_phone,
                "medical_history": patient_profile.medical_history,
                "insurance_info": patient_profile.insurance_info,
                "recent_appointments": appointments_data,
                "medical_records": records_data,
                "created_at": patient_profile.created_at.isoformat(),
            }

            return Response({"success": True, "patient": patient_detail})

        except User.DoesNotExist:
            return Response(
                {"success": False, "error": "Patient not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error fetching patient detail: {e}")
            return Response(
                {"success": False, "error": "Unable to load patient details"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SearchViewSet(viewsets.ViewSet):
    """Global search functionality."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def all(self, request):
        """Global search across all content."""
        query = request.query_params.get("q", "").strip()
        if not query or len(query) < 2:
            return Response(
                {
                    "success": False,
                    "error": "Search query must be at least 2 characters",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_profile = UserProfile.objects.get(user=request.user)
            results = {
                "appointments": [],
                "medical_records": [],
                "doctors": [],
                "patients": [],
            }

            # Search appointments
            if user_profile.role == "doctor":
                appointments = Appointment.objects.filter(
                    doctor=request.user, patient__first_name__icontains=query
                ).select_related("patient")[:5]
            else:
                appointments = Appointment.objects.filter(
                    patient=request.user, doctor__first_name__icontains=query
                ).select_related("doctor")[:5]

            for apt in appointments:
                results["appointments"].append(
                    {
                        "id": apt.id,
                        "date": apt.appointment_date.strftime("%Y-%m-%d"),
                        "time": apt.start_time.strftime("%I:%M %p"),
                        "type": apt.get_appointment_type_display(),
                        "status": apt.status,
                        "other_party": (
                            apt.patient.get_full_name()
                            if user_profile.role == "doctor"
                            else f"Dr. {apt.doctor.get_full_name()}"
                        ),
                    }
                )

            # Search medical records (patients only)
            if user_profile.role == "patient":
                records = MedicalRecord.objects.filter(
                    appointment__patient=request.user, diagnosis__icontains=query
                ).select_related("appointment__doctor")[:5]

                for record in records:
                    results["medical_records"].append(
                        {
                            "id": record.id,
                            "date": record.created_at.strftime("%Y-%m-%d"),
                            "doctor": f"Dr. {record.doctor.get_full_name()}",
                            "diagnosis": (
                                record.diagnosis[:100] + "..."
                                if len(record.diagnosis) > 100
                                else record.diagnosis
                            ),
                        }
                    )

            # Search doctors (patients only)
            if user_profile.role == "patient":
                doctors = DoctorProfile.objects.filter(
                    Q(user_profile__user__first_name__icontains=query)
                    | Q(user_profile__user__last_name__icontains=query)
                    | Q(specialty__icontains=query),
                    is_available=True,
                ).select_related("user_profile__user")[:5]

                for doctor in doctors:
                    results["doctors"].append(
                        {
                            "id": doctor.user_profile.user.id,
                            "name": f"Dr. {doctor.user_profile.user.get_full_name()}",
                            "specialty": doctor.specialty,
                            "rating": float(doctor.rating),
                        }
                    )

            # Search patients (doctors only)
            if user_profile.role == "doctor":
                patients = User.objects.filter(
                    Q(first_name__icontains=query) | Q(last_name__icontains=query),
                    patient_appointments__doctor=request.user,
                ).distinct()[:5]

                for patient in patients:
                    results["patients"].append(
                        {
                            "id": patient.id,
                            "name": patient.get_full_name(),
                            "email": patient.email,
                        }
                    )

            return Response({"success": True, "results": results})

        except Exception as e:
            logger.error(f"Search error: {e}")
            return Response(
                {"success": False, "error": "Search failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ReportsViewSet(viewsets.ViewSet):
    """Generate and export reports."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def appointments_export(self, request):
        """Export appointments to CSV."""
        try:
            user_profile = UserProfile.objects.get(user=request.user)

            # Get date range from query params
            start_date = request.query_params.get("start_date")
            end_date = request.query_params.get("end_date")

            if user_profile.role == "doctor":
                queryset = Appointment.objects.filter(doctor=request.user)
            else:
                queryset = Appointment.objects.filter(patient=request.user)

            if start_date:
                queryset = queryset.filter(appointment_date__gte=start_date)
            if end_date:
                queryset = queryset.filter(appointment_date__lte=end_date)

            # Create CSV
            output = StringIO()
            writer = csv.writer(output)

            # Write header
            if user_profile.role == "doctor":
                writer.writerow(["Date", "Time", "Patient", "Type", "Status", "Notes"])
                for apt in queryset.select_related("patient"):
                    writer.writerow(
                        [
                            apt.appointment_date.strftime("%Y-%m-%d"),
                            apt.start_time.strftime("%I:%M %p"),
                            apt.patient.get_full_name(),
                            apt.get_appointment_type_display(),
                            apt.status,
                            apt.patient_notes[:100] if apt.patient_notes else "",
                        ]
                    )
            else:
                writer.writerow(["Date", "Time", "Doctor", "Type", "Status", "Notes"])
                for apt in queryset.select_related("doctor"):
                    writer.writerow(
                        [
                            apt.appointment_date.strftime("%Y-%m-%d"),
                            apt.start_time.strftime("%I:%M %p"),
                            f"Dr. {apt.doctor.get_full_name()}",
                            apt.get_appointment_type_display(),
                            apt.status,
                            apt.patient_notes[:100] if apt.patient_notes else "",
                        ]
                    )

            output.seek(0)
            response = HttpResponse(output.getvalue(), content_type="text/csv")
            response["Content-Disposition"] = (
                f'attachment; filename="appointments_{timezone.now().strftime("%Y%m%d")}.csv"'
            )
            return response

        except Exception as e:
            logger.error(f"Export error: {e}")
            return Response(
                {"success": False, "error": "Export failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def medical_records_export(self, request):
        """Export medical records to CSV (patients only)."""
        try:
            user_profile = UserProfile.objects.get(user=request.user)

            if user_profile.role != "patient":
                return Response(
                    {
                        "success": False,
                        "error": "Only patients can export medical records",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            records = MedicalRecord.objects.filter(
                appointment__patient=request.user
            ).select_related("appointment__doctor")

            # Create CSV
            output = StringIO()
            writer = csv.writer(output)

            writer.writerow(
                [
                    "Date",
                    "Doctor",
                    "Diagnosis",
                    "Treatment",
                    "Prescription",
                    "Follow-up Required",
                ]
            )
            for record in records:
                writer.writerow(
                    [
                        record.created_at.strftime("%Y-%m-%d"),
                        f"Dr. {record.doctor.get_full_name()}",
                        record.diagnosis,
                        record.treatment,
                        record.prescription,
                        "Yes" if record.follow_up_required else "No",
                    ]
                )

            output.seek(0)
            response = HttpResponse(output.getvalue(), content_type="text/csv")
            response["Content-Disposition"] = (
                f'attachment; filename="medical_records_{timezone.now().strftime("%Y%m%d")}.csv"'
            )
            return response

        except Exception as e:
            logger.error(f"Medical records export error: {e}")
            return Response(
                {"success": False, "error": "Export failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class StatisticsViewSet(viewsets.ViewSet):
    """System statistics and insights."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get summary statistics for current user."""
        try:
            user_profile = UserProfile.objects.get(user=request.user)

            if user_profile.role == "doctor":
                return self._get_doctor_statistics(request.user)
            else:
                return self._get_patient_statistics(request.user)

        except Exception as e:
            logger.error(f"Statistics error: {e}")
            return Response(
                {"success": False, "error": "Failed to load statistics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_doctor_statistics(self, user):
        """Get comprehensive statistics for doctors."""
        try:
            today = timezone.now().date()
            this_month = today.replace(day=1)
            last_month = (this_month - timedelta(days=1)).replace(day=1)

            stats = {
                # Basic counts
                "total_patients": User.objects.filter(patient_appointments__doctor=user)
                .distinct()
                .count(),
                "total_appointments": Appointment.objects.filter(doctor=user).count(),
                "appointments_this_month": Appointment.objects.filter(
                    doctor=user, appointment_date__gte=this_month
                ).count(),
                "appointments_last_month": Appointment.objects.filter(
                    doctor=user,
                    appointment_date__gte=last_month,
                    appointment_date__lt=this_month,
                ).count(),
                # Today's stats
                "appointments_today": Appointment.objects.filter(
                    doctor=user, appointment_date=today
                ).count(),
                "completed_today": Appointment.objects.filter(
                    doctor=user, appointment_date=today, status="completed"
                ).count(),
                # Review stats
                "average_rating": Review.objects.filter(doctor=user).aggregate(
                    avg=Avg("rating")
                )["avg"]
                or 0,
                "total_reviews": Review.objects.filter(doctor=user).count(),
                # Medical records
                "medical_records_created": MedicalRecord.objects.filter(
                    appointment__doctor=user
                ).count(),
                # Appointment types breakdown
                "appointment_types": dict(
                    Appointment.objects.filter(doctor=user)
                    .values_list("appointment_type")
                    .annotate(count=Count("id"))
                ),
                # Status breakdown
                "appointment_status": dict(
                    Appointment.objects.filter(doctor=user)
                    .values_list("status")
                    .annotate(count=Count("id"))
                ),
            }

            # Calculate month-over-month growth
            if stats["appointments_last_month"] > 0:
                growth = (
                    (
                        stats["appointments_this_month"]
                        - stats["appointments_last_month"]
                    )
                    / stats["appointments_last_month"]
                ) * 100
                stats["monthly_growth"] = round(growth, 1)
            else:
                stats["monthly_growth"] = 0

            return Response({"success": True, "statistics": stats})

        except Exception as e:
            logger.error(f"Doctor statistics error: {e}")
            return Response(
                {"success": False, "error": "Failed to load doctor statistics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_patient_statistics(self, user):
        """Get comprehensive statistics for patients."""
        try:
            today = timezone.now().date()
            this_year = today.replace(month=1, day=1)

            stats = {
                # Basic counts
                "total_appointments": Appointment.objects.filter(patient=user).count(),
                "completed_appointments": Appointment.objects.filter(
                    patient=user, status="completed"
                ).count(),
                "upcoming_appointments": Appointment.objects.filter(
                    patient=user,
                    appointment_date__gte=today,
                    status__in=["pending", "confirmed"],
                ).count(),
                # This year's activity
                "appointments_this_year": Appointment.objects.filter(
                    patient=user, appointment_date__gte=this_year
                ).count(),
                # Medical records
                "medical_records": MedicalRecord.objects.filter(
                    appointment__patient=user
                ).count(),
                "prescriptions": Prescription.objects.filter(
                    medical_record__appointment__patient=user
                ).count(),
                "active_prescriptions": Prescription.objects.filter(
                    medical_record__appointment__patient=user, is_active=True
                ).count(),
                # Health metrics (latest)
                "latest_vitals": self._get_latest_vitals(user),
                # Doctors seen
                "doctors_seen": User.objects.filter(doctor_appointments__patient=user)
                .distinct()
                .count(),
                # Appointment types
                "appointment_types": dict(
                    Appointment.objects.filter(patient=user)
                    .values_list("appointment_type")
                    .annotate(count=Count("id"))
                ),
            }

            return Response({"success": True, "statistics": stats})

        except Exception as e:
            logger.error(f"Patient statistics error: {e}")
            return Response(
                {"success": False, "error": "Failed to load patient statistics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_latest_vitals(self, user):
        """Get latest vital signs for patient."""
        try:
            latest_record = (
                MedicalRecord.objects.filter(appointment__patient=user)
                .order_by("-created_at")
                .first()
            )

            if not latest_record:
                return None

            return {
                "date": latest_record.created_at.strftime("%Y-%m-%d"),
                "blood_pressure": latest_record.blood_pressure,
                "heart_rate": latest_record.heart_rate,
                "temperature": (
                    float(latest_record.temperature)
                    if latest_record.temperature
                    else None
                ),
                "weight": float(latest_record.weight) if latest_record.weight else None,
                "height": float(latest_record.height) if latest_record.height else None,
                "bmi": latest_record.bmi,
            }

        except Exception:
            return None


class FileUploadViewSet(viewsets.ViewSet):
    """Handle file uploads."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=["post"])
    def avatar(self, request):
        """Upload user avatar."""
        try:
            user_profile = UserProfile.objects.get(user=request.user)

            if "avatar" not in request.FILES:
                return Response(
                    {"success": False, "error": "No avatar file provided"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            avatar_file = request.FILES["avatar"]

            # Validate file size (max 5MB)
            if avatar_file.size > 5 * 1024 * 1024:
                return Response(
                    {"success": False, "error": "File size must be less than 5MB"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate file type
            if not avatar_file.content_type.startswith("image/"):
                return Response(
                    {"success": False, "error": "File must be an image"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Save avatar
            user_profile.avatar = avatar_file
            user_profile.save()

            return Response(
                {
                    "success": True,
                    "message": "Avatar uploaded successfully",
                    "avatar_url": (
                        user_profile.avatar.url if user_profile.avatar else None
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Avatar upload error: {e}")
            return Response(
                {"success": False, "error": "Failed to upload avatar"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def medical_document(self, request):
        """Upload medical document (patients only)."""
        try:
            user_profile = UserProfile.objects.get(user=request.user)

            if user_profile.role != "patient":
                return Response(
                    {
                        "success": False,
                        "error": "Only patients can upload medical documents",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if "document" not in request.FILES:
                return Response(
                    {"success": False, "error": "No document file provided"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            document_file = request.FILES["document"]

            # Validate file size (max 10MB)
            if document_file.size > 10 * 1024 * 1024:
                return Response(
                    {"success": False, "error": "File size must be less than 10MB"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # For now, just return success
            # In a real implementation, you'd save to a medical documents model
            return Response(
                {
                    "success": True,
                    "message": "Document uploaded successfully",
                    "filename": document_file.name,
                }
            )

        except Exception as e:
            logger.error(f"Document upload error: {e}")
            return Response(
                {"success": False, "error": "Failed to upload document"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SystemViewSet(viewsets.ViewSet):
    """System-wide information and utilities."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def info(self, request):
        """Get system information."""
        return Response(
            {
                "success": True,
                "system": {
                    "version": "1.0.0",
                    "name": "CareBridge Healthcare Management System",
                    "api_version": "v1",
                    "current_time": timezone.now().isoformat(),
                    "user_count": User.objects.filter(is_active=True).count(),
                    "doctor_count": UserProfile.objects.filter(role="doctor").count(),
                    "patient_count": UserProfile.objects.filter(role="patient").count(),
                },
            }
        )

    @action(detail=False, methods=["get"])
    def health_check(self, request):
        """API health check endpoint."""
        try:
            # Test database connection
            User.objects.count()

            return Response(
                {
                    "success": True,
                    "status": "healthy",
                    "timestamp": timezone.now().isoformat(),
                    "database": "connected",
                }
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return Response(
                {
                    "success": False,
                    "status": "unhealthy",
                    "timestamp": timezone.now().isoformat(),
                    "database": "disconnected",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# Add these utility functions for available slots endpoint that matches frontend expectations


@csrf_exempt
@require_http_methods(["GET"])
def get_available_slots_ajax(request):
    """Get available time slots for AJAX requests (matches frontend expectations)."""
    try:
        doctor_id = request.GET.get("doctor_id")
        date_str = request.GET.get("date")

        if not doctor_id or not date_str:
            return JsonResponse({"success": False, "slots": []})

        try:
            apt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            doctor = User.objects.get(id=doctor_id)
        except (ValueError, User.DoesNotExist):
            return JsonResponse({"success": False, "slots": []})

        appointment_service = AppointmentService()
        slots = appointment_service.get_available_slots(doctor, apt_date)

        return JsonResponse(
            {"success": True, "slots": [slot.strftime("%I:%M %p") for slot in slots]}
        )

    except Exception as e:
        logger.error(f"Available slots error: {e}")
        return JsonResponse({"success": False, "slots": []})


@csrf_exempt
@require_http_methods(["GET"])
def get_available_doctors_ajax(request):
    """Get available doctors for AJAX requests (matches frontend expectations)."""
    try:
        specialty = request.GET.get("specialty")

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
                    "available": doctor_profile.is_available,
                }
            )

        return JsonResponse({"success": True, "doctors": doctors})
    except Exception as e:
        logger.error(f"Available doctors error: {e}")
        return JsonResponse({"success": False, "doctors": []})


class AppointmentBookingViewSet(viewsets.ViewSet):
    """ViewSet for appointment booking."""

    permission_classes = [IsPatient]
    throttle_classes = [AppointmentBookingThrottle]

    @action(detail=False, methods=["post"])
    def book(self, request):
        """Book a new appointment."""
        serializer = AppointmentBookingSerializer(data=request.data)
        if serializer.is_valid():
            appointment_service = AppointmentService()

            try:
                appointment = appointment_service.book_appointment(
                    patient=request.user,
                    doctor_id=serializer.validated_data["doctor_id"],
                    appointment_date=serializer.validated_data["appointment_date"],
                    start_time=serializer.validated_data["start_time"],
                    appointment_type=serializer.validated_data["appointment_type"],
                    patient_notes=serializer.validated_data.get("patient_notes", ""),
                )

                return Response(
                    {
                        "success": True,
                        "message": "Appointment booked successfully!",
                        "appointment": AppointmentSerializer(appointment).data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    {"success": False, "error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=["get"])
    def available_doctors(self, request):
        """Get available doctors."""
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
                }
            )

        return Response({"success": True, "doctors": doctors})
