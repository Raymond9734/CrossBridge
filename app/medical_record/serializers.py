from rest_framework import serializers
from .models import MedicalRecord, Prescription, LabResult, Review


class PrescriptionSerializer(serializers.ModelSerializer):
    """Serializer for Prescription model."""

    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = [
            "id",
            "medication_name",
            "dosage",
            "frequency",
            "duration",
            "instructions",
            "quantity",
            "refills",
            "is_generic_allowed",
            "is_active",
            "date_prescribed",
            "date_filled",
            "patient_name",
            "doctor_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "date_prescribed", "created_at", "updated_at"]

    def get_patient_name(self, obj):
        return obj.patient.get_full_name()

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.get_full_name()}"


class LabResultSerializer(serializers.ModelSerializer):
    """Serializer for LabResult model."""

    is_abnormal = serializers.ReadOnlyField()

    class Meta:
        model = LabResult
        fields = [
            "id",
            "test_name",
            "test_type",
            "result_value",
            "result_unit",
            "reference_range",
            "status",
            "notes",
            "ordered_date",
            "result_date",
            "is_abnormal",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_result_date(self, value):
        """Validate result date is not before ordered date."""
        if value and hasattr(self, "initial_data"):
            ordered_date = self.initial_data.get("ordered_date")
            if ordered_date and value < ordered_date:
                raise serializers.ValidationError(
                    "Result date cannot be before ordered date"
                )
        return value


class MedicalRecordSerializer(serializers.ModelSerializer):
    """Serializer for MedicalRecord model."""

    prescriptions = PrescriptionSerializer(many=True, read_only=True)
    lab_results = LabResultSerializer(many=True, read_only=True)
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    bmi = serializers.ReadOnlyField()
    blood_pressure = serializers.ReadOnlyField()
    vitals_summary = serializers.SerializerMethodField()

    class Meta:
        model = MedicalRecord
        fields = [
            "id",
            "appointment",
            "diagnosis",
            "treatment",
            "prescription",
            "lab_results",
            "follow_up_required",
            "follow_up_date",
            "blood_pressure_systolic",
            "blood_pressure_diastolic",
            "heart_rate",
            "temperature",
            "weight",
            "height",
            "allergies",
            "medications",
            "medical_history",
            "is_sensitive",
            "prescriptions",
            "patient_name",
            "doctor_name",
            "bmi",
            "blood_pressure",
            "vitals_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_patient_name(self, obj):
        return obj.patient.get_full_name()

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.get_full_name()}"

    def get_vitals_summary(self, obj):
        return obj.get_vitals_summary()

    def validate_follow_up_date(self, value):
        """Validate follow-up date is in the future if follow-up is required."""
        if value and self.instance:
            if value <= self.instance.appointment.appointment_date:
                raise serializers.ValidationError(
                    "Follow-up date must be after the appointment date"
                )
        return value


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model."""

    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "patient",
            "doctor",
            "appointment",
            "rating",
            "review_text",
            "communication_rating",
            "professionalism_rating",
            "wait_time_rating",
            "is_verified",
            "is_anonymous",
            "patient_name",
            "doctor_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_verified", "created_at", "updated_at"]

    def get_patient_name(self, obj):
        return "Anonymous" if obj.is_anonymous else obj.patient.get_full_name()

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.get_full_name()}"

    def validate(self, data):
        """Validate review data."""
        # Ensure patient was actually seen by this doctor
        if data.get("appointment"):
            appointment = data["appointment"]
            if (
                appointment.patient != data["patient"]
                or appointment.doctor != data["doctor"]
            ):
                raise serializers.ValidationError(
                    "Review must be for an appointment between this patient and doctor"
                )

            if appointment.status != "completed":
                raise serializers.ValidationError(
                    "Can only review completed appointments"
                )

        return data
