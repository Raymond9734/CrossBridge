# api/v1/views/medical_records.py
"""
Medical Records management ViewSets for API v1
"""

from rest_framework.decorators import action
from rest_framework import status
from datetime import datetime

from .base import BaseModelViewSet
from app.appointment.models import Appointment
from app.medical_record.models import MedicalRecord
from app.medical_record.serializers import (
    MedicalRecordSerializer,
)
from app.medical_record.services import (
    MedicalRecordService,
)
from app.core.permissions import IsDoctor, IsDoctorOrPatient

import logging

logger = logging.getLogger(__name__)


class MedicalRecordViewSet(BaseModelViewSet):
    """ViewSet for medical records."""

    serializer_class = MedicalRecordSerializer
    permission_classes = [IsDoctorOrPatient]

    def get_queryset(self):
        """Filter medical records based on user role."""
        user = self.request.user

        try:
            profile = self.get_user_profile()
            if not profile:
                return MedicalRecord.objects.none()

            if profile.role == "doctor":
                return MedicalRecord.objects.filter(appointment__doctor=user)
            else:
                return MedicalRecord.objects.filter(appointment__patient=user)
        except Exception:
            return MedicalRecord.objects.none()

    def list(self, request):
        """List medical records with proper response format."""
        try:
            user_profile = self.get_user_profile()
            if not user_profile:
                return self.error_response(
                    "User profile not found", status_code=status.HTTP_404_NOT_FOUND
                )

            if user_profile.role == "doctor":
                records = (
                    MedicalRecord.objects.filter(appointment__doctor=request.user)
                    .select_related("appointment", "appointment__patient")
                    .prefetch_related("prescriptions", "lab_results_records")[:50]
                )
            else:
                records = (
                    MedicalRecord.objects.filter(appointment__patient=request.user)
                    .select_related("appointment", "appointment__doctor")
                    .prefetch_related("prescriptions", "lab_results_records")[:50]
                )

            records_data = []
            for record in records:
                records_data.append(
                    {
                        "id": record.id,
                        "appointment_id": record.appointment.id,
                        "patient_name": record.patient.get_full_name(),
                        "doctor_name": f"Dr. {record.doctor.get_full_name()}",
                        "appointment_date": record.appointment.appointment_date.strftime(
                            "%Y-%m-%d"
                        ),
                        "appointment_type": record.appointment.get_appointment_type_display(),
                        "diagnosis": record.diagnosis,
                        "treatment": record.treatment,
                        "prescription": record.prescription,
                        "follow_up_required": record.follow_up_required,
                        "follow_up_date": (
                            record.follow_up_date.strftime("%Y-%m-%d")
                            if record.follow_up_date
                            else None
                        ),
                        "blood_pressure": record.blood_pressure,
                        "heart_rate": record.heart_rate,
                        "temperature": (
                            str(record.temperature) if record.temperature else None
                        ),
                        "weight": str(record.weight) if record.weight else None,
                        "height": str(record.height) if record.height else None,
                        "bmi": record.bmi,
                        "created_at": record.created_at.isoformat(),
                    }
                )

            return self.success_response(data={"medical_records": records_data})

        except Exception as e:
            return self.handle_exception(e, "Unable to load medical records")

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ["create", "update", "partial_update"]:
            # Only doctors can create/update medical records
            permission_classes = [IsDoctor]
        else:
            permission_classes = [IsDoctorOrPatient]

        return [permission() for permission in permission_classes]

    def create(self, request):
        """Create medical record (doctor only)."""
        try:
            # Verify user is a doctor
            user_profile = self.get_user_profile()
            if not user_profile or user_profile.role != "doctor":
                return self.error_response(
                    "Only doctors can create medical records",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            appointment_id = request.data.get("appointment_id")
            if not appointment_id:
                return self.error_response(
                    "Appointment ID is required",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            try:
                appointment = Appointment.objects.get(
                    id=appointment_id, doctor=request.user
                )
            except Appointment.DoesNotExist:
                return self.error_response(
                    "Appointment not found or access denied",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            # Check if medical record already exists
            if hasattr(appointment, "medical_record"):
                return self.error_response(
                    "Medical record already exists for this appointment",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Extract vitals and other data
            vitals_data = {
                "blood_pressure_systolic": request.data.get("blood_pressure_systolic"),
                "blood_pressure_diastolic": request.data.get(
                    "blood_pressure_diastolic"
                ),
                "heart_rate": request.data.get("heart_rate"),
                "temperature": request.data.get("temperature"),
                "weight": request.data.get("weight"),
                "height": request.data.get("height"),
            }

            medical_record_service = MedicalRecordService()
            record = medical_record_service.create_record(
                appointment=appointment,
                diagnosis=request.data.get("diagnosis", ""),
                treatment=request.data.get("treatment", ""),
                vitals=vitals_data,
            )

            # Additional fields
            record.prescription = request.data.get("prescription", "")
            record.lab_results = request.data.get("lab_results", "")
            record.allergies = request.data.get("allergies", "")
            record.medications = request.data.get("medications", "")
            record.medical_history = request.data.get("medical_history", "")
            record.follow_up_required = request.data.get("follow_up_required", False)

            if record.follow_up_required and request.data.get("follow_up_date"):
                record.follow_up_date = datetime.strptime(
                    request.data.get("follow_up_date"), "%Y-%m-%d"
                ).date()

            record.save()

            return self.success_response(
                data={"medical_record": MedicalRecordSerializer(record).data},
                message="Medical record created successfully",
                status_code=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to create medical record")

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get medical records summary for current user."""
        try:
            user_profile = self.get_user_profile()
            if not user_profile:
                return self.error_response("User profile not found", status_code=404)

            if user_profile.role == "doctor":
                total_records = MedicalRecord.objects.filter(
                    appointment__doctor=request.user
                ).count()
                recent_records = MedicalRecord.objects.filter(
                    appointment__doctor=request.user
                ).order_by("-created_at")[:5]
            else:
                total_records = MedicalRecord.objects.filter(
                    appointment__patient=request.user
                ).count()
                recent_records = MedicalRecord.objects.filter(
                    appointment__patient=request.user
                ).order_by("-created_at")[:5]

            recent_data = []
            for record in recent_records:
                recent_data.append(
                    {
                        "id": record.id,
                        "date": record.created_at.strftime("%Y-%m-%d"),
                        "diagnosis": (
                            record.diagnosis[:100] + "..."
                            if len(record.diagnosis) > 100
                            else record.diagnosis
                        ),
                        "doctor_name": f"Dr. {record.doctor.get_full_name()}",
                        "patient_name": record.patient.get_full_name(),
                    }
                )

            return self.success_response(
                data={
                    "summary": {
                        "total_records": total_records,
                        "recent_records": recent_data,
                    }
                }
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to get medical records summary")
