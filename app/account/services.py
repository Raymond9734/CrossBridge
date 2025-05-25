from django.contrib.auth.models import User
from django.db import transaction
from django.core.cache import cache
from app.core.services import BaseService
from .models import UserProfile, DoctorProfile


class UserProfileService(BaseService):
    """Service for user profile operations."""

    def get_model(self):
        return UserProfile

    # account/services.py
    def create_patient_profile(self, user_data, profile_data):
        """Create a patient user and profile."""
        with transaction.atomic():
            # Create user
            user = User.objects.create_user(
                username=user_data["email"].split("@")[0],
                email=user_data["email"],
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name", ""),
                password=user_data["password"],
            )

            # Get the profile created by the signal and update it
            profile = user.userprofile
            profile.role = "patient"
            for key, value in profile_data.items():
                setattr(profile, key, value)
            profile.save()

            self.logger.info(f"Created patient profile for user {user.email}")
            return profile

    def create_doctor_profile(self, user_data, profile_data, doctor_data):
        """Create a doctor user and profiles."""
        with transaction.atomic():
            # Create user
            user = User.objects.create_user(
                username=user_data["email"].split("@")[0],
                email=user_data["email"],
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name", ""),
                password=user_data["password"],
            )

            # Update UserProfile
            profile = user.userprofile
            profile.role = "doctor"
            for key, value in profile_data.items():
                setattr(profile, key, value)
            profile.save()

            # Create DoctorProfile with the provided specialty
            DoctorProfile.objects.create(
                user_profile=profile,
                license_number=doctor_data.get("license_number", f"LIC-{user.id:06d}"),
                specialty=doctor_data.get("specialty", "General Medicine"),
                years_experience=doctor_data.get("years_experience", 0),
                bio=doctor_data.get("bio", ""),
                is_available=True,
                accepts_new_patients=True,
                consultation_fee=doctor_data.get("consultation_fee", 150.00),
            )

            self.logger.info(
                f"Created doctor profile for user {user.email} with specialty: {doctor_data.get('specialty')}"
            )
            return profile

    def update_profile(self, profile, data):
        """Update user profile."""
        user_data = data.pop("user", {})

        with transaction.atomic():
            # Update user fields
            user = profile.user
            for key, value in user_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.save()

            # Update profile fields
            for key, value in data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            profile.save()

            # Clear cache
            cache.delete(f"user_data:{user.id}")

            self.logger.info(f"Updated profile for user {user.email}")
            return profile

    def get_doctors_by_specialty(self, specialty=None):
        """Get doctors by specialty."""
        cache_key = f"doctors_by_specialty:{specialty or 'all'}"

        def get_doctors():
            queryset = UserProfile.objects.get_available_doctors()
            if specialty:
                queryset = queryset.filter(
                    doctorprofile__specialty__icontains=specialty
                )
            return queryset

        return self.get_cached(cache_key, get_doctors, timeout=600)


class DoctorProfileService(BaseService):
    """Service for doctor profile operations."""

    def get_model(self):
        return DoctorProfile

    def update_availability(self, doctor_profile, is_available):
        """Update doctor availability."""
        doctor_profile.is_available = is_available
        doctor_profile.save()

        # Clear related cache
        cache.delete(f"doctor_availability:{doctor_profile.user_profile.user.id}")
        cache.delete("doctors_by_specialty:all")

        self.logger.info(
            f"Updated availability for doctor {doctor_profile.user_profile.full_name}"
        )
        return doctor_profile

    def get_patient_statistics(self, doctor_user):
        """Get statistics for doctor's patients."""
        from app.appointment.models import Appointment

        cache_key = f"doctor_patient_stats:{doctor_user.id}"

        def get_stats():
            total_patients = (
                User.objects.filter(patient_appointments__doctor=doctor_user)
                .distinct()
                .count()
            )

            total_appointments = Appointment.objects.filter(doctor=doctor_user).count()

            completed_appointments = Appointment.objects.filter(
                doctor=doctor_user, status="completed"
            ).count()

            return {
                "total_patients": total_patients,
                "total_appointments": total_appointments,
                "completed_appointments": completed_appointments,
            }

        return self.get_cached(cache_key, get_stats, timeout=3600)
