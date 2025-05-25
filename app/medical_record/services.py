from django.db import transaction
from django.core.cache import cache
from app.core.services import BaseService
from app.core.exceptions import ValidationError
from .models import MedicalRecord


class MedicalRecordService(BaseService):
    """Service for medical record operations."""

    def get_model(self):
        return MedicalRecord

    def create_record(self, appointment, diagnosis="", treatment="", vitals=None):
        """Create a medical record for an appointment."""
        if hasattr(appointment, "medical_record"):
            raise ValidationError("Medical record already exists for this appointment")

        vitals = vitals or {}

        with transaction.atomic():
            record = self.create(
                appointment=appointment,
                diagnosis=diagnosis,
                treatment=treatment,
                **vitals,
            )

            # Mark appointment as completed
            appointment.status = "completed"
            appointment.save()

            # Clear cache
            self._clear_medical_record_cache(
                appointment.patient.id, appointment.doctor.id
            )

            return record

    def update_record(self, record, data):
        """Update a medical record."""
        with transaction.atomic():
            for key, value in data.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            record.save()

            # Clear cache
            self._clear_medical_record_cache(record.patient.id, record.doctor.id)

            return record

    def get_patient_records(self, patient, limit=None):
        """Get medical records for a patient."""
        cache_key = f"patient_medical_records:{patient.id}:{limit or 'all'}"

        def get_records():
            queryset = (
                MedicalRecord.objects.for_patient(patient)
                .select_related("appointment", "appointment__doctor")
                .prefetch_related("prescriptions", "lab_results")
            )

            if limit:
                queryset = queryset[:limit]

            return list(queryset)

        return self.get_cached(cache_key, get_records, timeout=600)

    def get_doctor_records(self, doctor, limit=None):
        """Get medical records for a doctor."""
        cache_key = f"doctor_medical_records:{doctor.id}:{limit or 'all'}"

        def get_records():
            queryset = (
                MedicalRecord.objects.for_doctor(doctor)
                .select_related("appointment", "appointment__patient")
                .prefetch_related("prescriptions", "lab_results")
            )

            if limit:
                queryset = queryset[:limit]

            return list(queryset)

        return self.get_cached(cache_key, get_records, timeout=600)

    def _clear_medical_record_cache(self, patient_id, doctor_id):
        """Clear medical record cache."""
        cache_keys = [
            f"patient_medical_records:{patient_id}:*",
            f"doctor_medical_records:{doctor_id}:*",
        ]

        for key_pattern in cache_keys:
            cache.delete_many(cache.keys(key_pattern))
