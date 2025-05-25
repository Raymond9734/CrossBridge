# api/v1/views/appointments.py
"""
Appointment management ViewSets for API v1
"""

from rest_framework.decorators import action
from rest_framework import status
from django.contrib.auth.models import User
from datetime import datetime

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitExceededError,
    ValidationError,
)

from .base import BaseAPIViewSet, BaseModelViewSet
from app.account.models import DoctorProfile
from app.appointment.models import Appointment
from app.appointment.serializers import (
    AppointmentSerializer,
    AppointmentBookingSerializer,
)
from app.appointment.services import AppointmentService
from app.core.permissions import (
    IsPatient,
    IsDoctorOrPatient,
    AppointmentBookingThrottle,
)

import logging

logger = logging.getLogger(__name__)


class AppointmentViewSet(BaseModelViewSet):
    """ViewSet for appointments."""

    serializer_class = AppointmentSerializer
    permission_classes = [IsDoctorOrPatient]

    def get_queryset(self):
        """Filter appointments based on user role."""
        user = self.request.user

        try:
            profile = self.get_user_profile()
            if not profile:
                return Appointment.objects.none()

            if profile.role == "doctor":
                queryset = Appointment.objects.filter(doctor=user)
            else:
                queryset = Appointment.objects.filter(patient=user)
        except Exception:
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

            return self.success_response(data={"appointments": appointments_data})

        except Exception as e:
            return self.handle_exception(e, "Unable to load appointments")

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
                    return self.error_response(
                        "Invalid doctor name format",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )
            except User.DoesNotExist:
                return self.error_response(
                    "Doctor not found", status_code=status.HTTP_404_NOT_FOUND
                )

            # Parse date and time
            try:
                apt_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
                apt_time = datetime.strptime(appointment_time, "%I:%M %p").time()
            except ValueError:
                return self.error_response(
                    "Invalid date or time format",
                    status_code=status.HTTP_400_BAD_REQUEST,
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

            return self.success_response(
                data={"appointment": AppointmentSerializer(appointment).data},
                message="Appointment booked successfully!",
                status_code=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return self.handle_exception(e, str(e))

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """Confirm an appointment (doctor only)."""
        try:
            appointment = self.get_object()

            # Only doctor can confirm
            if request.user != appointment.doctor:
                return self.error_response(
                    "Only the doctor can confirm appointments",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            appointment_service = AppointmentService()
            appointment_service.confirm_appointment(appointment)

            return self.success_response(message="Appointment confirmed successfully")

        except Exception as e:
            return self.handle_exception(e, "Failed to confirm appointment")

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel an appointment."""
        try:
            appointment = self.get_object()
            reason = request.data.get("reason", "")

            # Check if user can cancel this appointment
            if request.user not in [appointment.patient, appointment.doctor]:
                return self.error_response(
                    "Permission denied", status_code=status.HTTP_403_FORBIDDEN
                )

            appointment_service = AppointmentService()
            appointment_service.cancel_appointment(appointment, request.user, reason)

            return self.success_response(message="Appointment cancelled successfully")

        except Exception as e:
            return self.handle_exception(e, "Failed to cancel appointment")

    @action(detail=True, methods=["post"])
    def reschedule(self, request, pk=None):
        """Reschedule an appointment."""
        try:
            appointment = self.get_object()
            new_date = request.data.get("new_date")
            new_time = request.data.get("new_time")

            # Check if user can reschedule this appointment
            if request.user not in [appointment.patient, appointment.doctor]:
                return self.error_response(
                    "Permission denied", status_code=status.HTTP_403_FORBIDDEN
                )

            if not new_date or not new_time:
                return self.error_response(
                    "New date and time are required",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Parse new date and time
            try:
                new_apt_date = datetime.strptime(new_date, "%Y-%m-%d").date()
                new_apt_time = datetime.strptime(new_time, "%I:%M %p").time()
            except ValueError:
                return self.error_response(
                    "Invalid date or time format",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Check if new slot is available
            appointment_service = AppointmentService()
            if not appointment_service.is_slot_available(
                appointment.doctor, new_apt_date, new_apt_time
            ):
                return self.error_response(
                    "Selected time slot is not available",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Update appointment
            appointment.appointment_date = new_apt_date
            appointment.start_time = new_apt_time
            # Calculate new end time (30 minutes later)
            end_datetime = datetime.combine(new_apt_date, new_apt_time)
            from datetime import timedelta

            end_datetime += timedelta(minutes=30)
            appointment.end_time = end_datetime.time()
            appointment.save()

            return self.success_response(
                data={"appointment": AppointmentSerializer(appointment).data},
                message="Appointment rescheduled successfully",
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to reschedule appointment")

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """Get upcoming appointments for current user."""
        try:
            from django.utils import timezone

            profile = self.get_user_profile()
            if not profile:
                return self.error_response("User profile not found", status_code=404)

            today = timezone.now().date()

            if profile.role == "doctor":
                queryset = Appointment.objects.filter(
                    doctor=request.user,
                    appointment_date__gte=today,
                    status__in=["pending", "confirmed"],
                )
            else:
                queryset = Appointment.objects.filter(
                    patient=request.user,
                    appointment_date__gte=today,
                    status__in=["pending", "confirmed"],
                )

            appointments_data = []
            for apt in queryset.order_by("appointment_date", "start_time")[:10]:
                appointments_data.append(
                    {
                        "id": apt.id,
                        "patient": apt.patient.get_full_name(),
                        "doctor": f"Dr. {apt.doctor.get_full_name()}",
                        "date": apt.appointment_date.strftime("%Y-%m-%d"),
                        "time": apt.start_time.strftime("%I:%M %p"),
                        "type": apt.get_appointment_type_display(),
                        "status": apt.status,
                        "notes": apt.patient_notes,
                    }
                )

            return self.success_response(data={"appointments": appointments_data})

        except Exception as e:
            return self.handle_exception(e, "Failed to get upcoming appointments")

    @action(detail=False, methods=["get"])
    def history(self, request):
        """Get appointment history for current user."""
        try:
            profile = self.get_user_profile()
            if not profile:
                return self.error_response("User profile not found", status_code=404)

            if profile.role == "doctor":
                queryset = Appointment.objects.filter(
                    doctor=request.user,
                    status__in=["completed", "cancelled", "no_show"],
                )
            else:
                queryset = Appointment.objects.filter(
                    patient=request.user,
                    status__in=["completed", "cancelled", "no_show"],
                )

            # Pagination
            page_size = int(request.query_params.get("page_size", 20))
            page = int(request.query_params.get("page", 1))
            offset = (page - 1) * page_size

            total_count = queryset.count()
            appointments = queryset.order_by("-appointment_date", "-start_time")[
                offset : offset + page_size
            ]

            appointments_data = []
            for apt in appointments:
                appointments_data.append(
                    {
                        "id": apt.id,
                        "patient": apt.patient.get_full_name(),
                        "doctor": f"Dr. {apt.doctor.get_full_name()}",
                        "date": apt.appointment_date.strftime("%Y-%m-%d"),
                        "time": apt.start_time.strftime("%I:%M %p"),
                        "type": apt.get_appointment_type_display(),
                        "status": apt.status,
                        "notes": apt.patient_notes,
                    }
                )

            return self.success_response(
                data={
                    "appointments": appointments_data,
                    "pagination": {
                        "total": total_count,
                        "page": page,
                        "page_size": page_size,
                        "total_pages": (total_count + page_size - 1) // page_size,
                    },
                }
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to get appointment history")


class AppointmentBookingViewSet(BaseAPIViewSet):
    """ViewSet for appointment booking."""

    permission_classes = [IsPatient]
    throttle_classes = [AppointmentBookingThrottle]

    @action(detail=False, methods=["post"])
    def book(self, request):
        """Book a new appointment with enhanced error handling."""
        try:
            serializer = AppointmentBookingSerializer(data=request.data)
            if serializer.is_valid():
                appointment_service = AppointmentService()

                appointment = appointment_service.book_appointment(
                    patient=request.user,
                    doctor_id=serializer.validated_data["doctor_id"],
                    appointment_date=serializer.validated_data["appointment_date"],
                    start_time=serializer.validated_data["start_time"],
                    appointment_type=serializer.validated_data["appointment_type"],
                    patient_notes=serializer.validated_data.get("patient_notes", ""),
                )

                return self.success_response(
                    data={"appointment": AppointmentSerializer(appointment).data},
                    message="Appointment booked successfully!",
                    status_code=status.HTTP_201_CREATED,
                )

            return self.error_response(
                "Invalid booking data provided",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        except ValidationError as e:
            # Handle validation errors (e.g., invalid data, business rule violations)
            logger.warning(
                f"Appointment booking validation error for user {request.user.id}: {e}"
            )
            return self.error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="validation_error",
            )

        except ConflictError as e:
            # Handle conflict errors (e.g., time slot no longer available, doctor unavailable)
            logger.warning(
                f"Appointment booking conflict for user {request.user.id}: {e}"
            )
            return self.error_response(
                message=str(e),
                status_code=status.HTTP_409_CONFLICT,
                error_code="conflict_error",
            )

        except PermissionDeniedError as e:
            # Handle permission errors (e.g., trying to book with unavailable doctor)
            logger.warning(
                f"Appointment booking permission denied for user {request.user.id}: {e}"
            )
            return self.error_response(
                message=str(e),
                status_code=status.HTTP_403_FORBIDDEN,
                error_code="permission_denied",
            )

        except NotFoundError as e:
            # Handle not found errors (e.g., doctor doesn't exist)
            logger.warning(
                f"Appointment booking resource not found for user {request.user.id}: {e}"
            )
            return self.error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND,
                error_code="not_found",
            )

        except RateLimitExceededError as e:
            # Handle rate limiting errors
            logger.warning(
                f"Rate limit exceeded for appointment booking by user {request.user.id}: {e}"
            )
            return self.error_response(
                message="Too many booking attempts. Please wait before trying again.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                error_code="rate_limit_exceeded",
            )

        except Exception as e:
            # Generic fallback for unexpected errors
            logger.error(
                f"Unexpected error during appointment booking for user {request.user.id}: {e}"
            )
            return self.error_response(
                message="An unexpected error occurred while booking the appointment. Please try again.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code="internal_error",
            )

    @action(detail=False, methods=["get"])
    def available_doctors(self, request):
        """Get available doctors."""
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
                    }
                )

            return self.success_response(data={"doctors": doctors})

        except Exception as e:
            return self.handle_exception(e, "Failed to get available doctors")

    @action(detail=False, methods=["get"])
    def available_slots(self, request):
        """Get available time slots for a doctor on a specific date."""
        try:
            doctor_id = request.query_params.get("doctor_id")
            date_str = request.query_params.get("date")

            if not doctor_id or not date_str:
                return self.error_response(
                    "Doctor ID and date are required",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            try:
                doctor = User.objects.get(id=doctor_id)
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except (User.DoesNotExist, ValueError):
                return self.error_response(
                    "Invalid doctor ID or date format",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            appointment_service = AppointmentService()
            slots = appointment_service.get_available_slots(doctor, date)

            return self.success_response(
                data={
                    "date": date_str,
                    "slots": [slot.strftime("%I:%M %p") for slot in slots],
                }
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to get available slots")
