# api/v1/views/dashboard.py
"""
Dashboard ViewSets for API v1
"""

from rest_framework.decorators import action
from django.utils import timezone

from .base import BaseAPIViewSet
from app.account.services import DoctorProfileService
from app.appointment.models import Appointment
from app.appointment.services import AppointmentService
from app.medical_record.services import MedicalRecordService
from app.notification.services import NotificationService

import logging

logger = logging.getLogger(__name__)


class DashboardViewSet(BaseAPIViewSet):
    """Dashboard data endpoints."""

    @action(detail=False, methods=["get"])
    def data(self, request):
        """Get dashboard data based on user role."""
        try:
            user_profile = self.get_user_profile()
            if not user_profile:
                return self.error_response("User profile not found", status_code=404)

            if user_profile.role == "doctor":
                dashboard_data = self._get_doctor_dashboard_data(request.user)
            else:
                dashboard_data = self._get_patient_dashboard_data(request.user)

            # Get notifications
            notification_service = NotificationService()
            notifications = notification_service.get_user_notifications(
                request.user, unread_only=True, limit=10
            )

            notifications_data = {
                "unread_count": len(notifications),
                "items": [
                    {
                        "id": notif.id,
                        "type": notif.notification_type,
                        "title": notif.title,
                        "message": notif.message,
                        "created_at": notif.created_at.isoformat(),
                    }
                    for notif in notifications
                ],
            }

            dashboard_data.update(
                {
                    "user": {
                        "id": request.user.id,
                        "name": request.user.get_full_name(),
                        "email": request.user.email,
                        "role": user_profile.role,
                    },
                    "notifications": notifications_data,
                }
            )

            return self.success_response(data={"data": dashboard_data})

        except Exception as e:
            return self.handle_exception(e, "Unable to load dashboard data")

    def _get_patient_dashboard_data(self, user):
        """Get dashboard data for patients"""
        try:
            appointment_service = AppointmentService()
            medical_record_service = MedicalRecordService()

            # Get upcoming appointments
            upcoming_appointments = appointment_service.get_patient_appointments(
                user, status="confirmed"
            )[:5]

            # Get recent medical records
            recent_records = medical_record_service.get_patient_records(user, limit=5)

            # Format appointments
            appointments_data = []
            for apt in upcoming_appointments:
                appointments_data.append(
                    {
                        "id": apt.id,
                        "doctor": f"Dr. {apt.doctor.get_full_name()}",
                        "type": apt.get_appointment_type_display(),
                        "date": apt.appointment_date.strftime("%Y-%m-%d"),
                        "time": apt.start_time.strftime("%I:%M %p"),
                        "status": apt.status,
                    }
                )

            # Format medical records
            records_data = []
            for record in recent_records:
                records_data.append(
                    {
                        "id": record.id,
                        "title": (
                            record.diagnosis[:50] + "..."
                            if record.diagnosis and len(record.diagnosis) > 50
                            else record.diagnosis or "General Consultation"
                        ),
                        "doctor": f"Dr. {record.doctor.get_full_name()}",
                        "date": record.created_at.strftime("%B %d, %Y"),
                    }
                )

            # Get statistics
            total_appointments = Appointment.objects.filter(patient=user).count()
            completed_appointments = Appointment.objects.filter(
                patient=user, status="completed"
            ).count()

            return {
                "stats": {
                    "upcoming_appointments": len(upcoming_appointments),
                    "completed_visits": completed_appointments,
                    "total_appointments": total_appointments,
                },
                "appointments": appointments_data,
                "medical_records": records_data,
            }

        except Exception as e:
            logger.error(f"Error getting patient dashboard data: {e}")
            return {
                "stats": {
                    "upcoming_appointments": 0,
                    "completed_visits": 0,
                    "total_appointments": 0,
                },
                "appointments": [],
                "medical_records": [],
            }

    def _get_doctor_dashboard_data(self, user):
        """Get dashboard data for doctors"""
        try:
            appointment_service = AppointmentService()
            doctor_service = DoctorProfileService()
            today = timezone.now().date()

            # Get today's appointments
            todays_appointments = appointment_service.get_doctor_appointments(
                user, date=today
            )

            # Format appointments
            appointments_data = []
            for apt in todays_appointments:
                appointments_data.append(
                    {
                        "id": apt.id,
                        "patient": apt.patient.get_full_name(),
                        "type": apt.get_appointment_type_display(),
                        "time": apt.start_time.strftime("%I:%M %p"),
                        "status": apt.status,
                    }
                )

            # Get statistics
            stats = doctor_service.get_patient_statistics(user)

            return {
                "stats": {
                    "todays_appointments": len(todays_appointments),
                    "total_patients": stats.get("total_patients", 0),
                    "pending_reviews": stats.get("pending_reviews", 0),
                },
                "appointments": appointments_data,
                "patients": [],  # Will be loaded separately via patients endpoint
            }

        except Exception as e:
            logger.error(f"Error getting doctor dashboard data: {e}")
            return {
                "stats": {
                    "todays_appointments": 0,
                    "total_patients": 0,
                    "pending_reviews": 0,
                },
                "appointments": [],
                "patients": [],
            }

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get detailed statistics for dashboard widgets."""
        try:
            user_profile = self.get_user_profile()
            if not user_profile:
                return self.error_response("User profile not found", status_code=404)

            if user_profile.role == "doctor":
                stats = self._get_doctor_detailed_stats(request.user)
            else:
                stats = self._get_patient_detailed_stats(request.user)

            return self.success_response(data={"stats": stats})

        except Exception as e:
            return self.handle_exception(e, "Failed to load statistics")

    def _get_patient_detailed_stats(self, user):
        """Get detailed statistics for patients"""
        try:

            today = timezone.now().date()
            this_month = today.replace(day=1)

            return {
                "appointments": {
                    "total": Appointment.objects.filter(patient=user).count(),
                    "completed": Appointment.objects.filter(
                        patient=user, status="completed"
                    ).count(),
                    "upcoming": Appointment.objects.filter(
                        patient=user,
                        appointment_date__gte=today,
                        status__in=["pending", "confirmed"],
                    ).count(),
                    "this_month": Appointment.objects.filter(
                        patient=user, appointment_date__gte=this_month
                    ).count(),
                },
                "health": {
                    "medical_records": user.patient_appointments.filter(
                        medical_record__isnull=False
                    ).count(),
                    "active_prescriptions": 0,  # Would need prescription model
                    "last_checkup": self._get_last_checkup_date(user),
                },
            }
        except Exception:
            return {"appointments": {}, "health": {}}

    def _get_doctor_detailed_stats(self, user):
        """Get detailed statistics for doctors"""
        try:
            from datetime import timedelta

            today = timezone.now().date()
            this_month = today.replace(day=1)

            return {
                "appointments": {
                    "today": Appointment.objects.filter(
                        doctor=user, appointment_date=today
                    ).count(),
                    "this_week": Appointment.objects.filter(
                        doctor=user, appointment_date__gte=today - timedelta(days=7)
                    ).count(),
                    "this_month": Appointment.objects.filter(
                        doctor=user, appointment_date__gte=this_month
                    ).count(),
                    "total": Appointment.objects.filter(doctor=user).count(),
                },
                "patients": {
                    "total": user.doctor_appointments.values("patient")
                    .distinct()
                    .count(),
                    "new_this_month": user.doctor_appointments.filter(
                        appointment_date__gte=this_month
                    )
                    .values("patient")
                    .distinct()
                    .count(),
                },
                "performance": {
                    "avg_rating": 4.5,  # Would come from reviews
                    "total_reviews": 0,  # Would come from reviews
                    "completion_rate": self._calculate_completion_rate(user),
                },
            }
        except Exception:
            return {"appointments": {}, "patients": {}, "performance": {}}

    def _get_last_checkup_date(self, user):
        """Get patient's last checkup date"""
        try:
            last_appointment = (
                Appointment.objects.filter(patient=user, status="completed")
                .order_by("-appointment_date")
                .first()
            )

            return (
                last_appointment.appointment_date.strftime("%Y-%m-%d")
                if last_appointment
                else None
            )
        except Exception:
            return None

    def _calculate_completion_rate(self, doctor):
        """Calculate appointment completion rate for doctor"""
        try:
            total = Appointment.objects.filter(doctor=doctor).count()
            completed = Appointment.objects.filter(
                doctor=doctor, status="completed"
            ).count()

            return round((completed / total) * 100, 1) if total > 0 else 0
        except Exception:
            return 0
