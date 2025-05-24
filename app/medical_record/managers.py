from django.db import models
from django.utils import timezone
from datetime import timedelta
from app.core.managers import CacheableManager


class MedicalRecordManager(CacheableManager):
    """Custom manager for MedicalRecord model."""

    def for_patient(self, patient):
        """Get medical records for a specific patient."""
        return self.filter(appointment__patient=patient)

    def for_doctor(self, doctor):
        """Get medical records for a specific doctor."""
        return self.filter(appointment__doctor=doctor)

    def requiring_follow_up(self):
        """Get records requiring follow-up."""
        return self.filter(follow_up_required=True)

    def with_diagnosis(self):
        """Get records that have a diagnosis."""
        return self.exclude(diagnosis="")

    def recent(self, days=30):
        """Get recent medical records."""
        cutoff_date = timezone.now().date() - timedelta(days=days)
        return self.filter(created_at__date__gte=cutoff_date)


class PrescriptionManager(models.Manager):
    """Custom manager for Prescription model."""

    def active(self):
        """Get active prescriptions."""
        return self.filter(is_active=True)

    def for_patient(self, patient):
        """Get prescriptions for a specific patient."""
        return self.filter(medical_record__appointment__patient=patient)

    def for_medication(self, medication_name):
        """Get prescriptions for a specific medication."""
        return self.filter(medication_name__icontains=medication_name)


class LabResultManager(models.Manager):
    """Custom manager for LabResult model."""

    def abnormal(self):
        """Get abnormal lab results."""
        return self.filter(status__in=["abnormal", "critical"])

    def for_patient(self, patient):
        """Get lab results for a specific patient."""
        return self.filter(medical_record__appointment__patient=patient)

    def by_test_type(self, test_type):
        """Get lab results by test type."""
        return self.filter(test_type=test_type)


class ReviewManager(models.Manager):
    """Custom manager for Review model."""

    def for_doctor(self, doctor):
        """Get reviews for a specific doctor."""
        return self.filter(doctor=doctor)

    def verified(self):
        """Get verified reviews only."""
        return self.filter(is_verified=True)

    def average_rating(self, doctor):
        """Get average rating for a doctor."""
        result = self.for_doctor(doctor).aggregate(avg_rating=models.Avg("rating"))
        return result["avg_rating"] or 0
