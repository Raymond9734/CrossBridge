from django.db import models
# from app.account.models import DoctorProfile
from app.core.managers import CacheableManager


class UserProfileManager(CacheableManager):
    """Custom manager for UserProfile model."""

    def get_patients(self):
        """Get all patient profiles."""
        return self.filter(role="patient")

    def get_doctors(self):
        """Get all doctor profiles."""
        return self.filter(role="doctor")

    def get_available_doctors(self):
        """Get available doctors."""
        return self.filter(
            role="doctor", doctorprofile__is_available=True
        ).select_related("doctorprofile")

    def create_profile(self, user, role="patient", **extra_fields):
        """Create a user profile with additional fields."""
        profile = self.create(user=user, role=role, **extra_fields)

        # Create doctor profile if role is doctor
        if role == "doctor":
            from .models import DoctorProfile

            DoctorProfile.objects.create(
                user_profile=profile,
                license_number=f"LIC-{user.id:06d}",
                specialty="General Medicine",
            )

        return profile


class DoctorProfileManager(models.Manager):
    """Custom manager for DoctorProfile model."""

    def get_available(self):
        """Get available doctors."""
        return self.filter(is_available=True)

    def by_specialty(self, specialty):
        """Get doctors by specialty."""
        return self.filter(specialty__icontains=specialty)

    def accepting_patients(self):
        """Get doctors accepting new patients."""
        return self.filter(accepts_new_patients=True, is_available=True)


# Update models to use custom managers
# UserProfile.add_to_class("objects", UserProfileManager())
# UserProfile.object1 = UserProfileManager()
# DoctorProfile.add_to_class("objects", DoctorProfileManager())
