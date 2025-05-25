# api/v1/views/system.py
"""
System utilities and advanced features ViewSets for API v1
"""

from rest_framework.decorators import action
from rest_framework import status
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .base import BaseAPIViewSet
from app.account.models import UserProfile, DoctorProfile
from app.appointment.models import Appointment
from app.medical_record.models import MedicalRecord

import logging

logger = logging.getLogger(__name__)


class SearchViewSet(BaseAPIViewSet):
    """Global search functionality."""

    @action(detail=False, methods=["get"])
    def all(self, request):
        """Global search across all content."""
        query = request.query_params.get("q", "").strip()
        if not query or len(query) < 2:
            return self.error_response(
                "Search query must be at least 2 characters",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_profile = self.get_user_profile()
            if not user_profile:
                return self.error_response("User profile not found", status_code=404)

            results = {
                "appointments": [],
                "medical_records": [],
                "doctors": [],
                "patients": [],
            }

            # Search appointments
            if user_profile.role == "doctor":
                appointments = Appointment.objects.filter(
                    doctor=request.user, patient__first_name__icontains=query
                ).select_related("patient")[:5]
            else:
                appointments = Appointment.objects.filter(
                    patient=request.user, doctor__first_name__icontains=query
                ).select_related("doctor")[:5]

            for apt in appointments:
                results["appointments"].append(
                    {
                        "id": apt.id,
                        "date": apt.appointment_date.strftime("%Y-%m-%d"),
                        "time": apt.start_time.strftime("%I:%M %p"),
                        "type": apt.get_appointment_type_display(),
                        "status": apt.status,
                        "other_party": (
                            apt.patient.get_full_name()
                            if user_profile.role == "doctor"
                            else f"Dr. {apt.doctor.get_full_name()}"
                        ),
                    }
                )

            # Search medical records (patients only)
            if user_profile.role == "patient":
                records = MedicalRecord.objects.filter(
                    appointment__patient=request.user, diagnosis__icontains=query
                ).select_related("appointment__doctor")[:5]

                for record in records:
                    results["medical_records"].append(
                        {
                            "id": record.id,
                            "date": record.created_at.strftime("%Y-%m-%d"),
                            "doctor": f"Dr. {record.doctor.get_full_name()}",
                            "diagnosis": (
                                record.diagnosis[:100] + "..."
                                if len(record.diagnosis) > 100
                                else record.diagnosis
                            ),
                        }
                    )

            # Search doctors (patients only)
            if user_profile.role == "patient":
                doctors = DoctorProfile.objects.filter(
                    Q(user_profile__user__first_name__icontains=query)
                    | Q(user_profile__user__last_name__icontains=query)
                    | Q(specialty__icontains=query),
                    is_available=True,
                ).select_related("user_profile__user")[:5]

                for doctor in doctors:
                    results["doctors"].append(
                        {
                            "id": doctor.user_profile.user.id,
                            "name": f"Dr. {doctor.user_profile.user.get_full_name()}",
                            "specialty": doctor.specialty,
                            "rating": float(doctor.rating),
                        }
                    )

            # Search patients (doctors only)
            if user_profile.role == "doctor":
                patients = User.objects.filter(
                    Q(first_name__icontains=query) | Q(last_name__icontains=query),
                    patient_appointments__doctor=request.user,
                ).distinct()[:5]

                for patient in patients:
                    results["patients"].append(
                        {
                            "id": patient.id,
                            "name": patient.get_full_name(),
                            "email": patient.email,
                        }
                    )

            return self.success_response(data={"results": results})

        except Exception as e:
            return self.handle_exception(e, "Search failed")


class StatisticsViewSet(BaseAPIViewSet):
    """System statistics and insights."""

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get summary statistics for current user."""
        try:
            user_profile = self.get_user_profile()
            if not user_profile:
                return self.error_response("User profile not found", status_code=404)

            if user_profile.role == "doctor":
                return self._get_doctor_statistics(request.user)
            else:
                return self._get_patient_statistics(request.user)

        except Exception as e:
            return self.handle_exception(e, "Failed to load statistics")

    def _get_doctor_statistics(self, user):
        """Get comprehensive statistics for doctors."""
        try:
            today = timezone.now().date()
            this_month = today.replace(day=1)
            last_month = (this_month - timedelta(days=1)).replace(day=1)

            stats = {
                # Basic counts
                "total_patients": User.objects.filter(patient_appointments__doctor=user)
                .distinct()
                .count(),
                "total_appointments": Appointment.objects.filter(doctor=user).count(),
                "appointments_this_month": Appointment.objects.filter(
                    doctor=user, appointment_date__gte=this_month
                ).count(),
                "appointments_last_month": Appointment.objects.filter(
                    doctor=user,
                    appointment_date__gte=last_month,
                    appointment_date__lt=this_month,
                ).count(),
                # Today's stats
                "appointments_today": Appointment.objects.filter(
                    doctor=user, appointment_date=today
                ).count(),
                "completed_today": Appointment.objects.filter(
                    doctor=user, appointment_date=today, status="completed"
                ).count(),
                # Medical records
                "medical_records_created": MedicalRecord.objects.filter(
                    appointment__doctor=user
                ).count(),
                # Appointment types breakdown
                "appointment_types": dict(
                    Appointment.objects.filter(doctor=user)
                    .values_list("appointment_type")
                    .annotate(count=Count("id"))
                ),
                # Status breakdown
                "appointment_status": dict(
                    Appointment.objects.filter(doctor=user)
                    .values_list("status")
                    .annotate(count=Count("id"))
                ),
            }

            # Calculate month-over-month growth
            if stats["appointments_last_month"] > 0:
                growth = (
                    (
                        stats["appointments_this_month"]
                        - stats["appointments_last_month"]
                    )
                    / stats["appointments_last_month"]
                ) * 100
                stats["monthly_growth"] = round(growth, 1)
            else:
                stats["monthly_growth"] = 0

            return self.success_response(data={"statistics": stats})

        except Exception as e:
            return self.handle_exception(e, "Failed to load doctor statistics")

    def _get_patient_statistics(self, user):
        """Get comprehensive statistics for patients."""
        try:
            today = timezone.now().date()
            this_year = today.replace(month=1, day=1)

            stats = {
                # Basic counts
                "total_appointments": Appointment.objects.filter(patient=user).count(),
                "completed_appointments": Appointment.objects.filter(
                    patient=user, status="completed"
                ).count(),
                "upcoming_appointments": Appointment.objects.filter(
                    patient=user,
                    appointment_date__gte=today,
                    status__in=["pending", "confirmed"],
                ).count(),
                # This year's activity
                "appointments_this_year": Appointment.objects.filter(
                    patient=user, appointment_date__gte=this_year
                ).count(),
                # Medical records
                "medical_records": MedicalRecord.objects.filter(
                    appointment__patient=user
                ).count(),
                # Health metrics (latest)
                "latest_vitals": self._get_latest_vitals(user),
                # Doctors seen
                "doctors_seen": User.objects.filter(doctor_appointments__patient=user)
                .distinct()
                .count(),
                # Appointment types
                "appointment_types": dict(
                    Appointment.objects.filter(patient=user)
                    .values_list("appointment_type")
                    .annotate(count=Count("id"))
                ),
            }

            return self.success_response(data={"statistics": stats})

        except Exception as e:
            return self.handle_exception(e, "Failed to load patient statistics")

    def _get_latest_vitals(self, user):
        """Get latest vital signs for patient."""
        try:
            latest_record = (
                MedicalRecord.objects.filter(appointment__patient=user)
                .order_by("-created_at")
                .first()
            )

            if not latest_record:
                return None

            return {
                "date": latest_record.created_at.strftime("%Y-%m-%d"),
                "blood_pressure": latest_record.blood_pressure,
                "heart_rate": latest_record.heart_rate,
                "temperature": (
                    float(latest_record.temperature)
                    if latest_record.temperature
                    else None
                ),
                "weight": float(latest_record.weight) if latest_record.weight else None,
                "height": float(latest_record.height) if latest_record.height else None,
                "bmi": latest_record.bmi,
            }

        except Exception:
            return None


class SystemViewSet(BaseAPIViewSet):
    """System-wide information and utilities."""

    @action(detail=False, methods=["get"])
    def info(self, request):
        """Get system information."""
        return self.success_response(
            data={
                "system": {
                    "version": "1.0.0",
                    "name": "CareBridge Healthcare Management System",
                    "api_version": "v1",
                    "current_time": timezone.now().isoformat(),
                    "user_count": User.objects.filter(is_active=True).count(),
                    "doctor_count": UserProfile.objects.filter(role="doctor").count(),
                    "patient_count": UserProfile.objects.filter(role="patient").count(),
                }
            }
        )

    @action(detail=False, methods=["get"])
    def health_check(self, request):
        """API health check endpoint."""
        try:
            # Test database connection
            User.objects.count()

            return self.success_response(
                data={
                    "status": "healthy",
                    "timestamp": timezone.now().isoformat(),
                    "database": "connected",
                }
            )
        except Exception as e:
            return self.error_response(
                "System unhealthy",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                errors={"database": "disconnected", "error": str(e)},
            )
