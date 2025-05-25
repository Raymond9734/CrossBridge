from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Appointment, DoctorAvailability


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for DoctorAvailability model."""

    doctor_name = serializers.SerializerMethodField()
    day_name = serializers.SerializerMethodField()

    class Meta:
        model = DoctorAvailability
        fields = [
            "id",
            "doctor",
            "doctor_name",
            "day_of_week",
            "day_name",
            "start_time",
            "end_time",
            "is_available",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.user_profile.full_name}"

    def get_day_name(self, obj):
        return obj.get_day_of_week_display()

    def validate(self, data):
        """Validate availability data."""
        if data["start_time"] >= data["end_time"]:
            raise serializers.ValidationError("End time must be after start time")
        return data


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for Appointment model."""

    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    duration_minutes = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    can_be_cancelled = serializers.ReadOnlyField()

    class Meta:
        model = Appointment
        fields = [
            "id",
            "appointment_id",
            "patient",
            "doctor",
            "patient_name",
            "doctor_name",
            "appointment_date",
            "start_time",
            "end_time",
            "appointment_type",
            "status",
            "patient_notes",
            "doctor_notes",
            "duration_minutes",
            "is_upcoming",
            "can_be_cancelled",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "appointment_id",
            "duration_minutes",
            "is_upcoming",
            "can_be_cancelled",
            "created_at",
            "updated_at",
        ]

    def get_patient_name(self, obj):
        return obj.patient.get_full_name()

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.get_full_name()}"

    def validate_appointment_date(self, value):
        """Validate appointment date."""
        if value < timezone.now().date():
            raise serializers.ValidationError(
                "Cannot schedule appointments in the past"
            )
        return value

    def validate(self, data):
        """Validate appointment data."""
        # Check if start time is before end time
        if data["start_time"] >= data["end_time"]:
            raise serializers.ValidationError("End time must be after start time")

        # Check for conflicts
        conflicts = Appointment.objects.conflicting_appointments(
            doctor=data["doctor"],
            date=data["appointment_date"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            exclude_id=self.instance.id if self.instance else None,
        )

        if conflicts:
            raise serializers.ValidationError(
                "Doctor has a conflicting appointment at this time"
            )

        return data


class AppointmentBookingSerializer(serializers.Serializer):
    """Serializer for appointment booking requests."""

    doctor_id = serializers.IntegerField()
    appointment_date = serializers.DateField()
    start_time = serializers.TimeField()
    appointment_type = serializers.ChoiceField(choices=Appointment.APPOINTMENT_TYPES)
    patient_notes = serializers.CharField(
        required=False, allow_blank=True, max_length=1000
    )

    def validate_appointment_date(self, value):
        """Validate appointment date."""
        if value < timezone.now().date():
            raise serializers.ValidationError(
                "Cannot schedule appointments in the past"
            )

        # Don't allow booking too far in advance (e.g., 3 months)
        max_advance_date = timezone.now().date() + timedelta(days=90)
        if value > max_advance_date:
            raise serializers.ValidationError(
                "Cannot schedule appointments more than 3 months in advance"
            )

        return value

    def validate_doctor_id(self, value):
        """Validate doctor exists and is available."""
        try:
            from app.account.models import DoctorProfile

            doctor_profile = DoctorProfile.objects.get(user_profile__user__id=value)
            if not doctor_profile.is_available:
                raise serializers.ValidationError("Doctor is not currently available")
            return value
        except DoctorProfile.DoesNotExist:
            raise serializers.ValidationError("Doctor not found")

    def validate(self, data):
        """Validate booking data."""
        # Check if the requested time slot is available
        from .services import AppointmentService

        service = AppointmentService()
        doctor = User.objects.get(id=data["doctor_id"])
        available_slots = service.get_available_slots(doctor, data["appointment_date"])

        if data["start_time"] not in available_slots:
            raise serializers.ValidationError("Selected time slot is not available")

        return data


class AvailableSlotSerializer(serializers.Serializer):
    """Serializer for available time slots."""

    date = serializers.DateField()
    slots = serializers.ListField(child=serializers.TimeField())
