# api/v1/views/medical_records.py
"""
Medical Records management ViewSets for API v1
"""

from rest_framework.decorators import action
from rest_framework import status
from datetime import datetime

from .base import BaseModelViewSet
from app.appointment.models import Appointment
from app.medical_record.models import MedicalRecord, Prescription, LabResult
from app.medical_record.serializers import (
    MedicalRecordSerializer,
    PrescriptionSerializer,
    LabResultSerializer,
)
from app.medical_record.services import (
    MedicalRecordService,
    PrescriptionService,
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


class PrescriptionViewSet(BaseModelViewSet):
    """ViewSet for prescriptions."""

    serializer_class = PrescriptionSerializer
    permission_classes = [IsDoctorOrPatient]

    def get_queryset(self):
        """Filter prescriptions based on user role."""
        user = self.request.user

        try:
            profile = self.get_user_profile()
            if not profile:
                return Prescription.objects.none()

            if profile.role == "doctor":
                return Prescription.objects.filter(
                    medical_record__appointment__doctor=user
                )
            else:
                return Prescription.objects.filter(
                    medical_record__appointment__patient=user
                )
        except Exception:
            return Prescription.objects.none()

    def list(self, request):
        """List prescriptions with proper response format."""
        try:
            queryset = self.get_queryset()

            # Filter by active status if requested
            active_only = request.query_params.get("active_only")
            if active_only == "true":
                queryset = queryset.filter(is_active=True)

            prescriptions_data = []
            for prescription in queryset.select_related(
                "medical_record__appointment__patient",
                "medical_record__appointment__doctor",
            )[:50]:
                prescriptions_data.append(
                    {
                        "id": prescription.id,
                        "medication_name": prescription.medication_name,
                        "dosage": prescription.dosage,
                        "frequency": prescription.frequency,
                        "duration": prescription.duration,
                        "instructions": prescription.instructions,
                        "quantity": prescription.quantity,
                        "refills": prescription.refills,
                        "is_generic_allowed": prescription.is_generic_allowed,
                        "is_active": prescription.is_active,
                        "date_prescribed": prescription.date_prescribed.strftime(
                            "%Y-%m-%d"
                        ),
                        "date_filled": (
                            prescription.date_filled.strftime("%Y-%m-%d")
                            if prescription.date_filled
                            else None
                        ),
                        "patient_name": prescription.patient.get_full_name(),
                        "doctor_name": f"Dr. {prescription.doctor.get_full_name()}",
                    }
                )

            return self.success_response(data={"prescriptions": prescriptions_data})

        except Exception as e:
            return self.handle_exception(e, "Unable to load prescriptions")

    def get_permissions(self):
        """Only doctors can create/update prescriptions."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsDoctor]
        else:
            permission_classes = [IsDoctorOrPatient]

        return [permission() for permission in permission_classes]

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """Deactivate a prescription."""
        try:
            prescription = self.get_object()

            # Only prescribing doctor can deactivate
            if request.user != prescription.medical_record.appointment.doctor:
                return self.error_response(
                    "Permission denied", status_code=status.HTTP_403_FORBIDDEN
                )

            prescription_service = PrescriptionService()
            prescription_service.deactivate_prescription(prescription)

            return self.success_response(
                message="Prescription deactivated successfully"
            )

        except Exception as e:
            return self.handle_exception(e, "Failed to deactivate prescription")


class LabResultViewSet(BaseModelViewSet):
    """ViewSet for lab results."""

    serializer_class = LabResultSerializer
    permission_classes = [IsDoctorOrPatient]

    def get_queryset(self):
        """Filter lab results based on user role."""
        user = self.request.user

        try:
            profile = self.get_user_profile()
            if not profile:
                return LabResult.objects.none()

            if profile.role == "doctor":
                return LabResult.objects.filter(
                    medical_record__appointment__doctor=user
                )
            else:
                return LabResult.objects.filter(
                    medical_record__appointment__patient=user
                )
        except Exception:
            return LabResult.objects.none()

    def list(self, request):
        """List lab results with proper response format."""
        try:
            queryset = self.get_queryset()

            # Filter by test type if requested
            test_type = request.query_params.get("test_type")
            if test_type:
                queryset = queryset.filter(test_type=test_type)

            lab_results_data = []
            for result in queryset.select_related(
                "medical_record__appointment__patient",
                "medical_record__appointment__doctor",
            )[:50]:
                lab_results_data.append(
                    {
                        "id": result.id,
                        "test_name": result.test_name,
                        "test_type": result.get_test_type_display(),
                        "result_value": result.result_value,
                        "result_unit": result.result_unit,
                        "reference_range": result.reference_range,
                        "status": result.get_status_display(),
                        "notes": result.notes,
                        "ordered_date": result.ordered_date.strftime("%Y-%m-%d"),
                        "result_date": (
                            result.result_date.strftime("%Y-%m-%d")
                            if result.result_date
                            else None
                        ),
                        "is_abnormal": result.is_abnormal,
                        "patient_name": result.medical_record.patient.get_full_name(),
                    }
                )

            return self.success_response(data={"lab_results": lab_results_data})

        except Exception as e:
            return self.handle_exception(e, "Unable to load lab results")

    def get_permissions(self):
        """Only doctors can create/update lab results."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsDoctor]
        else:
            permission_classes = [IsDoctorOrPatient]

        return [permission() for permission in permission_classes]


# class ReviewViewSet(BaseModelViewSet):
#     """ViewSet for reviews."""

#     serializer_class = ReviewSerializer

#     def get_queryset(self):
#         """Filter reviews based on user role."""
#         user = self.request.user

#         try:
#             profile = self.get_user_profile()
#             if not profile:
#                 return Review.objects.none()

#             if profile.role == "doctor":
#                 return Review.objects.filter(doctor=user)
#             else:
#                 return Review.objects.filter(patient=user)
#         except Exception:
#             return Review.objects.none()

#     def list(self, request):
#         """List reviews with proper response format."""
#         try:
#             queryset = self.get_queryset()

#             # Filter by doctor if requested (for public viewing)
#             doctor_id = request.query_params.get("doctor_id")
#             if doctor_id:
#                 queryset = Review.objects.filter(doctor_id=doctor_id, is_verified=True)

#             reviews_data = []
#             for review in queryset.select_related("patient", "doctor", "appointment")[
#                 :50
#             ]:
#                 reviews_data.append(
#                     {
#                         "id": review.id,
#                         "rating": review.rating,
#                         "review_text": review.review_text,
#                         "communication_rating": review.communication_rating,
#                         "professionalism_rating": review.professionalism_rating,
#                         "wait_time_rating": review.wait_time_rating,
#                         "is_verified": review.is_verified,
#                         "is_anonymous": review.is_anonymous,
#                         "patient_name": (
#                             "Anonymous"
#                             if review.is_anonymous
#                             else review.patient.get_full_name()
#                         ),
#                         "doctor_name": f"Dr. {review.doctor.get_full_name()}",
#                         "created_at": review.created_at.strftime("%Y-%m-%d"),
#                     }
#                 )

#             return self.success_response(data={"reviews": reviews_data})

#         except Exception as e:
#             return self.handle_exception(e, "Unable to load reviews")

#     def get_permissions(self):
#         """Only patients can create reviews."""
#         if self.action in ["create"]:
#             permission_classes = [IsPatient]
#         else:
#             permission_classes = [self.permission_classes[0]]

#         return [permission() for permission in permission_classes]

#     def create(self, request):
#         """Create review (patient only)."""
#         try:
#             review_service = ReviewService()

#             doctor_id = request.data.get("doctor_id")
#             appointment_id = request.data.get("appointment_id")
#             rating = request.data.get("rating")

#             if not all([doctor_id, rating]):
#                 return self.error_response(
#                     "Doctor ID and rating are required",
#                     status_code=status.HTTP_400_BAD_REQUEST,
#                 )

#             try:
#                 doctor = User.objects.get(id=doctor_id, userprofile__role="doctor")
#             except User.DoesNotExist:
#                 return self.error_response(
#                     "Doctor not found", status_code=status.HTTP_404_NOT_FOUND
#                 )

#             appointment = None
#             if appointment_id:
#                 try:
#                     appointment = Appointment.objects.get(
#                         id=appointment_id,
#                         patient=request.user,
#                         doctor=doctor,
#                         status="completed",
#                     )
#                 except Appointment.DoesNotExist:
#                     return self.error_response(
#                         "Completed appointment not found",
#                         status_code=status.HTTP_404_NOT_FOUND,
#                     )

#             detailed_ratings = {
#                 "communication_rating": request.data.get("communication_rating"),
#                 "professionalism_rating": request.data.get("professionalism_rating"),
#                 "wait_time_rating": request.data.get("wait_time_rating"),
#             }

#             review = review_service.create_review(
#                 patient=request.user,
#                 doctor=doctor,
#                 appointment=appointment,
#                 rating=int(rating),
#                 review_text=request.data.get("review_text", ""),
#                 detailed_ratings=detailed_ratings,
#             )

#             return self.success_response(
#                 data={"review": ReviewSerializer(review).data},
#                 message="Review created successfully",
#                 status_code=status.HTTP_201_CREATED,
#             )

#         except Exception as e:
#             return self.handle_exception(e, str(e))
