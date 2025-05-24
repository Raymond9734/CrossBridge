from django.db import transaction
from django.core.cache import cache
from app.core.services import BaseService
from app.core.exceptions import ValidationError
from .models import MedicalRecord, Prescription, LabResult, Review


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


class PrescriptionService(BaseService):
    """Service for prescription operations."""

    def get_model(self):
        return Prescription

    def add_prescription(self, medical_record, medication_data):
        """Add a prescription to a medical record."""
        with transaction.atomic():
            prescription = self.create(medical_record=medical_record, **medication_data)

            # Clear cache
            cache.delete(f"patient_prescriptions:{medical_record.patient.id}")

            return prescription

    def get_patient_prescriptions(self, patient, active_only=True):
        """Get prescriptions for a patient."""
        cache_key = (
            f"patient_prescriptions:{patient.id}:{'active' if active_only else 'all'}"
        )

        def get_prescriptions():
            queryset = Prescription.objects.for_patient(patient)
            if active_only:
                queryset = queryset.active()
            return queryset.select_related("medical_record__appointment")

        return self.get_cached(cache_key, get_prescriptions, timeout=3600)

    def deactivate_prescription(self, prescription):
        """Deactivate a prescription."""
        prescription.is_active = False
        prescription.save()

        # Clear cache
        cache.delete(f"patient_prescriptions:{prescription.patient.id}")

        return prescription


class LabResultService(BaseService):
    """Service for lab result operations."""

    def get_model(self):
        return LabResult

    def add_lab_result(self, medical_record, test_data):
        """Add a lab result to a medical record."""
        with transaction.atomic():
            lab_result = self.create(medical_record=medical_record, **test_data)

            # Clear cache
            cache.delete(f"patient_lab_results:{medical_record.patient.id}")

            return lab_result

    def get_patient_lab_results(self, patient, test_type=None):
        """Get lab results for a patient."""
        cache_key = f"patient_lab_results:{patient.id}:{test_type or 'all'}"

        def get_results():
            queryset = LabResult.objects.for_patient(patient)
            if test_type:
                queryset = queryset.by_test_type(test_type)
            return queryset.select_related("medical_record__appointment")

        return self.get_cached(cache_key, get_results, timeout=1800)


class ReviewService(BaseService):
    """Service for review operations."""

    def get_model(self):
        return Review

    def create_review(
        self,
        patient,
        doctor,
        appointment,
        rating,
        review_text="",
        detailed_ratings=None,
    ):
        """Create a review for a doctor."""
        # Check if review already exists
        if Review.objects.filter(
            patient=patient, doctor=doctor, appointment=appointment
        ).exists():
            raise ValidationError("Review already exists for this appointment")

        # Verify appointment was completed
        if appointment.status != "completed":
            raise ValidationError("Can only review completed appointments")

        detailed_ratings = detailed_ratings or {}

        with transaction.atomic():
            review = self.create(
                patient=patient,
                doctor=doctor,
                appointment=appointment,
                rating=rating,
                review_text=review_text,
                **detailed_ratings,
            )

            # Update doctor's overall rating
            self._update_doctor_rating(doctor)

            return review

    def get_doctor_reviews(self, doctor, verified_only=False):
        """Get reviews for a doctor."""
        cache_key = (
            f"doctor_reviews:{doctor.id}:{'verified' if verified_only else 'all'}"
        )

        def get_reviews():
            queryset = Review.objects.for_doctor(doctor)
            if verified_only:
                queryset = queryset.verified()
            return queryset.select_related("patient", "appointment")

        return self.get_cached(cache_key, get_reviews, timeout=1800)

    def _update_doctor_rating(self, doctor):
        """Update doctor's overall rating."""
        try:
            from app.account.models import DoctorProfile

            doctor_profile = DoctorProfile.objects.get(user_profile__user=doctor)
            doctor_profile.update_rating()

            # Clear cache
            cache.delete(f"doctor_reviews:{doctor.id}:all")
            cache.delete(f"doctor_reviews:{doctor.id}:verified")
        except DoctorProfile.DoesNotExist:
            pass
