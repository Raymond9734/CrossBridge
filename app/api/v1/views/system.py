# api/v1/views/system.py
"""
System utilities and advanced features ViewSets for API v1
"""

from rest_framework.decorators import action
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
import csv
from io import StringIO

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


class ReportsViewSet(BaseAPIViewSet):
    """Generate and export reports."""

    @action(detail=False, methods=["get"])
    def appointments_export(self, request):
        """Export appointments to CSV."""
        try:
            user_profile = self.get_user_profile()
            if not user_profile:
                return self.error_response("User profile not found", status_code=404)

            # Get date range from query params
            start_date = request.query_params.get("start_date")
            end_date = request.query_params.get("end_date")

            if user_profile.role == "doctor":
                queryset = Appointment.objects.filter(doctor=request.user)
            else:
                queryset = Appointment.objects.filter(patient=request.user)

            if start_date:
                queryset = queryset.filter(appointment_date__gte=start_date)
            if end_date:
                queryset = queryset.filter(appointment_date__lte=end_date)

            # Create CSV
            output = StringIO()
            writer = csv.writer(output)

            # Write header
            if user_profile.role == "doctor":
                writer.writerow(["Date", "Time", "Patient", "Type", "Status", "Notes"])
                for apt in queryset.select_related("patient"):
                    writer.writerow(
                        [
                            apt.appointment_date.strftime("%Y-%m-%d"),
                            apt.start_time.strftime("%I:%M %p"),
                            apt.patient.get_full_name(),
                            apt.get_appointment_type_display(),
                            apt.status,
                            apt.patient_notes[:100] if apt.patient_notes else "",
                        ]
                    )
            else:
                writer.writerow(["Date", "Time", "Doctor", "Type", "Status", "Notes"])
                for apt in queryset.select_related("doctor"):
                    writer.writerow(
                        [
                            apt.appointment_date.strftime("%Y-%m-%d"),
                            apt.start_time.strftime("%I:%M %p"),
                            f"Dr. {apt.doctor.get_full_name()}",
                            apt.get_appointment_type_display(),
                            apt.status,
                            apt.patient_notes[:100] if apt.patient_notes else "",
                        ]
                    )

            output.seek(0)
            response = HttpResponse(output.getvalue(), content_type="text/csv")
            response["Content-Disposition"] = (
                f'attachment; filename="appointments_{timezone.now().strftime("%Y%m%d")}.csv"'
            )
            return response

        except Exception as e:
            return self.handle_exception(e, "Export failed")

    @action(detail=False, methods=["get"])
    def medical_records_export(self, request):
        """Export medical records to CSV (patients only)."""
        try:
            user_profile = self.get_user_profile()
            if not user_profile:
                return self.error_response("User profile not found", status_code=404)

            if user_profile.role != "patient":
                return self.error_response(
                    "Only patients can export medical records",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            records = MedicalRecord.objects.filter(
                appointment__patient=request.user
            ).select_related("appointment__doctor")

            # Create CSV
            output = StringIO()
            writer = csv.writer(output)

            writer.writerow(
                [
                    "Date",
                    "Doctor",
                    "Diagnosis",
                    "Treatment",
                    "Prescription",
                    "Follow-up Required",
                ]
            )
            for record in records:
                writer.writerow(
                    [
                        record.created_at.strftime("%Y-%m-%d"),
                        f"Dr. {record.doctor.get_full_name()}",
                        record.diagnosis,
                        record.treatment,
                        record.prescription,
                        "Yes" if record.follow_up_required else "No",
                    ]
                )

            output.seek(0)
            response = HttpResponse(output.getvalue(), content_type="text/csv")
            response["Content-Disposition"] = (
                f'attachment; filename="medical_records_{timezone.now().strftime("%Y%m%d")}.csv"'
            )
            return response

        except Exception as e:
            return self.handle_exception(e, "Export failed")

    @action(detail=False, methods=["get"])
    def generate_summary(self, request):
        """Generate a summary report for current user."""
        try:
            user_profile = self.get_user_profile()
            if not user_profile:
                return self.error_response("User profile not found", status_code=404)

            if user_profile.role == "doctor":
                summary = self._generate_doctor_summary(request.user)
            else:
                summary = self._generate_patient_summary(request.user)

            return self.success_response(data={"summary": summary})

        except Exception as e:
            return self.handle_exception(e, "Failed to generate summary")

    def _generate_doctor_summary(self, doctor):
        """Generate summary for doctor."""
        total_appointments = Appointment.objects.filter(doctor=doctor).count()
        total_patients = (
            User.objects.filter(patient_appointments__doctor=doctor).distinct().count()
        )

        today = timezone.now().date()
        this_month = today.replace(day=1)

        appointments_this_month = Appointment.objects.filter(
            doctor=doctor, appointment_date__gte=this_month
        ).count()

        return {
            "role": "doctor",
            "total_appointments": total_appointments,
            "total_patients": total_patients,
            "appointments_this_month": appointments_this_month,
            "generated_at": timezone.now().isoformat(),
        }

    def _generate_patient_summary(self, patient):
        """Generate summary for patient."""
        total_appointments = Appointment.objects.filter(patient=patient).count()
        completed_appointments = Appointment.objects.filter(
            patient=patient, status="completed"
        ).count()

        upcoming_appointments = Appointment.objects.filter(
            patient=patient,
            appointment_date__gte=timezone.now().date(),
            status__in=["pending", "confirmed"],
        ).count()

        medical_records_count = MedicalRecord.objects.filter(
            appointment__patient=patient
        ).count()

        return {
            "role": "patient",
            "total_appointments": total_appointments,
            "completed_appointments": completed_appointments,
            "upcoming_appointments": upcoming_appointments,
            "medical_records": medical_records_count,
            "generated_at": timezone.now().isoformat(),
        }


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


class FileUploadViewSet(BaseAPIViewSet):
    """Handle file uploads."""

    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=["post"])
    def avatar(self, request):
        """Upload user avatar."""
        try:
            user_profile = self.get_user_profile()
            if not user_profile:
                return self.error_response("User profile not found", status_code=404)

            if "avatar" not in request.FILES:
                return self.error_response(
                    "No avatar file provided", status_code=status.HTTP_400_BAD_REQUEST
                )

            avatar_file = request.FILES["avatar"]

            # Validate file size (max 5MB)
            if avatar_file.size > 5 * 1024 * 1024:
                return self.error_response(
                    "File size must be less than 5MB",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Validate file type
            if not avatar_file.content_type.startswith("image/"):
                return self.error_response(
                    "File must be an image", status_code=status.HTTP_400_BAD_REQUEST
                )

            # Save avatar
            user_profile.avatar = avatar_file
            user_profile.save()

            return self.success_response(
                data={
                    "avatar_url": (
                        user_profile.avatar.url if user_profile.avatar else None
                    )
                },
                message="Avatar uploaded successfully",
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to upload avatar")

    @action(detail=False, methods=["post"])
    def medical_document(self, request):
        """Upload medical document (patients only)."""
        try:
            user_profile = self.get_user_profile()
            if not user_profile:
                return self.error_response("User profile not found", status_code=404)

            if user_profile.role != "patient":
                return self.error_response(
                    "Only patients can upload medical documents",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            if "document" not in request.FILES:
                return self.error_response(
                    "No document file provided", status_code=status.HTTP_400_BAD_REQUEST
                )

            document_file = request.FILES["document"]

            # Validate file size (max 10MB)
            if document_file.size > 10 * 1024 * 1024:
                return self.error_response(
                    "File size must be less than 10MB",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # For now, just return success
            # In a real implementation, you'd save to a medical documents model
            return self.success_response(
                data={"filename": document_file.name},
                message="Document uploaded successfully",
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to upload document")


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
