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
