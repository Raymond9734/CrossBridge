from django.contrib.auth.models import User
from django.db import transaction
from django.core.cache import cache
from datetime import datetime, timedelta
from django.utils import timezone
from app.core.services import BaseService
from app.core.exceptions import NotFoundError, ValidationError, ConflictError
from .models import Appointment, DoctorAvailability


class AppointmentService(BaseService):
    """Service for appointment operations."""

    def get_model(self):
        return Appointment

    def book_appointment(
        self,
        patient,
        doctor_id,
        appointment_date,
        start_time,
        appointment_type,
        patient_notes="",
    ):
        """Book an appointment with proper exception handling."""
        try:
            doctor = User.objects.get(id=doctor_id)
        except User.DoesNotExist:
            raise NotFoundError("The selected doctor was not found.")

        # Validate doctor is actually a doctor
        try:
            doctor_profile = doctor.userprofile.doctorprofile
            if not doctor_profile.is_available:
                raise ValidationError(
                    "The selected doctor is currently not accepting new appointments."
                )
            if not doctor_profile.accepts_new_patients:
                raise ValidationError(
                    "The selected doctor is not accepting new patients at this time."
                )
        except AttributeError:
            raise ValidationError("The selected user is not a registered doctor.")

        # Calculate end time (default 30 minutes)
        start_datetime = datetime.combine(appointment_date, start_time)
        end_datetime = start_datetime + timedelta(minutes=30)
        end_time = end_datetime.time()

        # Check if appointment date is valid
        if appointment_date < timezone.now().date():
            raise ValidationError("Cannot schedule appointments in the past.")

        # Check if appointment is too far in the future (3 months)
        max_future_date = timezone.now().date() + timedelta(days=90)
        if appointment_date > max_future_date:
            raise ValidationError(
                "Cannot schedule appointments more than 3 months in advance."
            )

        # Check availability with more specific error messages
        if not self.is_slot_available(doctor, appointment_date, start_time):
            # Check if it's a weekend/holiday issue
            day_of_week = appointment_date.weekday()
            availability = DoctorAvailability.objects.filter(
                doctor__user_profile__user=doctor,
                day_of_week=day_of_week,
                is_available=True,
            ).first()

            if not availability:
                day_names = [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ]
                raise ConflictError(
                    f"Dr. {doctor.get_full_name()} is not available on {day_names[day_of_week]}s."
                )

            # Check if the time is outside available hours
            if (
                start_time < availability.start_time
                or start_time >= availability.end_time
            ):
                raise ConflictError(
                    f"The selected time is outside Dr. {doctor.get_full_name()}'s available hours "
                    f"({availability.start_time.strftime('%I:%M %p')} - {availability.end_time.strftime('%I:%M %p')})."
                )

            # Time slot is within hours but already booked
            raise ConflictError(
                "The selected time slot is no longer available. "
                "Please choose a different time or refresh the available slots."
            )

        # Check for patient's existing appointments (prevent double booking)
        existing_appointment = Appointment.objects.filter(
            patient=patient,
            appointment_date=appointment_date,
            start_time__lt=end_time,
            end_time__gt=start_time,
            status__in=["pending", "confirmed"],
        ).first()

        if existing_appointment:
            raise ConflictError(
                f"You already have an appointment scheduled at {existing_appointment.start_time.strftime('%I:%M %p')} "
                f"on {appointment_date.strftime('%B %d, %Y')}."
            )

        with transaction.atomic():
            try:
                appointment = self.create(
                    patient=patient,
                    doctor=doctor,
                    appointment_date=appointment_date,
                    start_time=start_time,
                    end_time=end_time,
                    appointment_type=appointment_type,
                    patient_notes=patient_notes,
                    created_by=patient,
                    status="pending",
                )

                # Clear cache
                self._clear_appointment_cache(patient.id, doctor.id)

                try:
                    from app.notification.services import NotificationService

                    notification_service = NotificationService()
                    notification_service.send_appointment_request_notification(
                        appointment
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to send appointment notification: {e}")

                return appointment

            except Exception as e:
                # Don't mask the real error with a misleading message
                if isinstance(e, (ValidationError, ConflictError, NotFoundError)):
                    raise  # Re-raise our custom exceptions as-is

                self.logger.error(f"Unexpected error during appointment booking: {e}")
                raise ConflictError(
                    "Unable to complete the booking due to a system error. Please try again."
                )

    def get_available_slots(self, doctor, date):
        """Get available time slots for a doctor on a specific date."""
        cache_key = f"available_slots:{doctor.id}:{date}"

        def get_slots():
            # Get doctor's availability for this day
            day_of_week = date.weekday()
            availability = DoctorAvailability.objects.filter(
                doctor__user_profile__user=doctor,
                day_of_week=day_of_week,
                is_available=True,
            ).first()

            if not availability:
                return []

            # Generate time slots
            slots = availability.get_time_slots()

            # Filter out booked slots
            booked_appointments = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=date,
                status__in=["pending", "confirmed", "in_progress"],
            )

            booked_times = {apt.start_time for apt in booked_appointments}
            available_slots = [slot for slot in slots if slot not in booked_times]

            return available_slots

        return self.get_cached(cache_key, get_slots, timeout=300)

    def is_slot_available(self, doctor, date, time):
        """Check if a specific time slot is available."""
        available_slots = self.get_available_slots(doctor, date)
        return time in available_slots

    def cancel_appointment(self, appointment, cancelled_by, reason=""):
        """Cancel an appointment."""
        if not appointment.can_be_cancelled:
            raise ValidationError("This appointment cannot be cancelled")

        appointment.cancel(cancelled_by, reason)

        # Clear cache
        self._clear_appointment_cache(appointment.patient.id, appointment.doctor.id)

        return appointment

    def confirm_appointment(self, appointment):
        """Confirm an appointment."""
        appointment.confirm()

        # Clear cache
        self._clear_appointment_cache(appointment.patient.id, appointment.doctor.id)

        return appointment

    def get_patient_appointments(self, patient, status=None):
        """Get appointments for a patient."""
        cache_key = f"patient_appointments:{patient.id}:{status or 'all'}"

        def get_appointments():
            return Appointment.objects.for_patient(patient, status).select_related(
                "doctor", "patient"
            )

        return self.get_cached(cache_key, get_appointments, timeout=300)

    def get_doctor_appointments(self, doctor, date=None):
        """Get appointments for a doctor."""
        cache_key = f"doctor_appointments:{doctor.id}:{date or 'all'}"

        def get_appointments():
            return Appointment.objects.for_doctor(doctor, date).select_related(
                "patient", "doctor"
            )

        return self.get_cached(cache_key, get_appointments, timeout=300)

    def _clear_appointment_cache(self, patient_id, doctor_id):
        """Clear appointment-related cache."""
        cache_keys = [
            f"patient_appointments:{patient_id}:*",
            f"doctor_appointments:{doctor_id}:*",
            f"available_slots:{doctor_id}:*",
        ]

        for key_pattern in cache_keys:
            cache.delete_many(cache.keys(key_pattern))


class DoctorAvailabilityService(BaseService):
    """Service for doctor availability operations."""

    def get_model(self):
        return DoctorAvailability

    def set_availability(
        self, doctor_profile, day_of_week, start_time, end_time, is_available=True
    ):
        """Set doctor availability for a specific day and time."""
        availability, created = self.get_or_create(
            doctor=doctor_profile,
            day_of_week=day_of_week,
            start_time=start_time,
            defaults={"end_time": end_time, "is_available": is_available},
        )

        if not created:
            availability.end_time = end_time
            availability.is_available = is_available
            availability.save()

        # Clear cache
        cache.delete(f"doctor_availability:{doctor_profile.user_profile.user.id}")
        cache.delete(f"available_slots:{doctor_profile.user_profile.user.id}:*")

        return availability

    def get_doctor_availability(self, doctor_profile):
        """Get all availability for a doctor."""
        cache_key = f"doctor_availability:{doctor_profile.user_profile.user.id}"

        def get_availability():
            return DoctorAvailability.objects.for_doctor(doctor_profile).order_by(
                "day_of_week", "start_time"
            )

        return self.get_cached(cache_key, get_availability, timeout=3600)

    def toggle_availability(self, availability_id):
        """Toggle availability status."""
        availability = self.get_object(id=availability_id)
        availability.is_available = not availability.is_available
        availability.save()

        # Clear cache
        doctor_id = availability.doctor.user_profile.user.id
        cache.delete(f"doctor_availability:{doctor_id}")
        cache.delete(f"available_slots:{doctor_id}:*")

        return availability
