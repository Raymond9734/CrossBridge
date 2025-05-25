from rest_framework import serializers
from .models import MedicalRecord


class MedicalRecordSerializer(serializers.ModelSerializer):
    """Serializer for MedicalRecord model."""

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
