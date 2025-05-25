# api/v1/views/patients.py
"""
Patient Management ViewSets for API v1
"""

from rest_framework.decorators import action
from rest_framework import status
from django.contrib.auth.models import User

from .base import BaseAPIViewSet
from app.appointment.models import Appointment
from app.medical_record.models import MedicalRecord
from app.core.permissions import IsDoctor

import logging

logger = logging.getLogger(__name__)


class PatientManagementViewSet(BaseAPIViewSet):
    """ViewSet for doctor patient management."""

    permission_classes = [IsDoctor]

    @action(detail=False, methods=["get"])
    def patients(self, request):
        """Get patients for current doctor."""
        try:
            # Get patients who have appointments with this doctor
            patients_query = (
                Appointment.objects.filter(doctor=request.user)
                .values("patient")
                .distinct()
            )

            patients_data = []
            for patient_data in patients_query:
                try:
                    patient = User.objects.get(id=patient_data["patient"])
                    patient_profile = patient.userprofile

                    # Get appointment stats
                    total_appointments = Appointment.objects.filter(
                        doctor=request.user, patient=patient
                    ).count()

                    last_appointment = (
                        Appointment.objects.filter(doctor=request.user, patient=patient)
                        .order_by("-appointment_date")
                        .first()
                    )

                    patients_data.append(
                        {
                            "id": patient.id,
                            "name": patient.get_full_name(),
                            "email": patient.email,
                            "phone": patient_profile.phone,
                            "date_of_birth": (
                                patient_profile.date_of_birth.strftime("%Y-%m-%d")
                                if patient_profile.date_of_birth
                                else None
                            ),
                            "gender": (
                                patient_profile.get_gender_display()
                                if patient_profile.gender
                                else None
                            ),
                            "address": patient_profile.address,
                            "emergency_contact": patient_profile.emergency_contact,
                            "emergency_phone": patient_profile.emergency_phone,
                            "medical_history": patient_profile.medical_history,
                            "insurance_info": patient_profile.insurance_info,
                            "total_appointments": total_appointments,
                            "last_visit": (
                                last_appointment.appointment_date.strftime("%Y-%m-%d")
                                if last_appointment
                                else None
                            ),
                            "created_at": patient_profile.created_at.isoformat(),
                        }
                    )
                except User.DoesNotExist:
                    continue

            return self.success_response(data={"patients": patients_data})

        except Exception as e:
            return self.handle_exception(e, "Unable to load patients")

    @action(detail=True, methods=["get"])
    def detail(self, request, pk=None):
        """Get detailed patient information."""
        try:
            patient = User.objects.get(id=pk)

            # Verify this doctor has treated this patient
            if not Appointment.objects.filter(
                doctor=request.user, patient=patient
            ).exists():
                return self.error_response(
                    "Patient not found", status_code=status.HTTP_404_NOT_FOUND
                )

            patient_profile = patient.userprofile

            # Get recent appointments
            recent_appointments = Appointment.objects.filter(
                doctor=request.user, patient=patient
            ).order_by("-appointment_date")[:10]

            appointments_data = []
            for apt in recent_appointments:
                appointments_data.append(
                    {
                        "id": apt.id,
                        "date": apt.appointment_date.strftime("%Y-%m-%d"),
                        "time": apt.start_time.strftime("%I:%M %p"),
                        "type": apt.get_appointment_type_display(),
                        "status": apt.status,
                    }
                )

            # Get medical records
            medical_records = MedicalRecord.objects.filter(
                appointment__doctor=request.user, appointment__patient=patient
            ).order_by("-created_at")[:10]

            records_data = []
            for record in medical_records:
                records_data.append(
                    {
                        "id": record.id,
                        "date": record.created_at.strftime("%Y-%m-%d"),
                        "diagnosis": record.diagnosis,
                        "treatment": record.treatment,
                        "appointment_type": record.appointment.get_appointment_type_display(),
                    }
                )

            patient_detail = {
                "id": patient.id,
                "name": patient.get_full_name(),
                "email": patient.email,
                "phone": patient_profile.phone,
                "date_of_birth": (
                    patient_profile.date_of_birth.strftime("%Y-%m-%d")
                    if patient_profile.date_of_birth
                    else None
                ),
                "gender": (
                    patient_profile.get_gender_display()
                    if patient_profile.gender
                    else None
                ),
                "address": patient_profile.address,
                "emergency_contact": patient_profile.emergency_contact,
                "emergency_phone": patient_profile.emergency_phone,
                "medical_history": patient_profile.medical_history,
                "insurance_info": patient_profile.insurance_info,
                "recent_appointments": appointments_data,
                "medical_records": records_data,
                "created_at": patient_profile.created_at.isoformat(),
            }

            return self.success_response(data={"patient": patient_detail})

        except User.DoesNotExist:
            return self.error_response(
                "Patient not found", status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return self.handle_exception(e, "Unable to load patient details")

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get patient statistics for current doctor."""
        try:
            # Total unique patients
            total_patients = (
                User.objects.filter(patient_appointments__doctor=request.user)
                .distinct()
                .count()
            )

            # New patients this month
            from django.utils import timezone

            this_month = timezone.now().date().replace(day=1)

            new_patients_this_month = (
                User.objects.filter(
                    patient_appointments__doctor=request.user,
                    patient_appointments__appointment_date__gte=this_month,
                )
                .distinct()
                .count()
            )

            # Active patients (with appointments in last 6 months)
            six_months_ago = (
                timezone.now()
                .date()
                .replace(
                    month=(
                        timezone.now().date().month - 6
                        if timezone.now().date().month > 6
                        else timezone.now().date().month + 6
                    ),
                    year=(
                        timezone.now().date().year - 1
                        if timezone.now().date().month <= 6
                        else timezone.now().date().year
                    ),
                )
            )

            active_patients = (
                User.objects.filter(
                    patient_appointments__doctor=request.user,
                    patient_appointments__appointment_date__gte=six_months_ago,
                )
                .distinct()
                .count()
            )

            # Patient demographics
            gender_stats = {}
            all_patients = User.objects.filter(
                patient_appointments__doctor=request.user
            ).distinct()

            for patient in all_patients:

                # gender = patient.userprofile.gender or "Unknown"
                gender_display = (
                    patient.userprofile.get_gender_display()
                    if patient.userprofile.gender
                    else "Unknown"
                )
                gender_stats[gender_display] = gender_stats.get(gender_display, 0) + 1

            # Age groups
            age_groups = {"0-18": 0, "19-35": 0, "36-55": 0, "56+": 0, "Unknown": 0}

            for patient in all_patients:

                if patient.userprofile.date_of_birth:
                    age = (
                        timezone.now().date() - patient.userprofile.date_of_birth
                    ).days // 365
                    if age <= 18:
                        age_groups["0-18"] += 1
                    elif age <= 35:
                        age_groups["19-35"] += 1
                    elif age <= 55:
                        age_groups["36-55"] += 1
                    else:
                        age_groups["56+"] += 1
                else:
                    age_groups["Unknown"] += 1

            stats = {
                "total_patients": total_patients,
                "new_patients_this_month": new_patients_this_month,
                "active_patients": active_patients,
                "demographics": {
                    "gender": gender_stats,
                    "age_groups": age_groups,
                },
            }

            return self.success_response(data={"stats": stats})

        except Exception as e:
            return self.handle_exception(e, "Unable to load patient statistics")

    @action(detail=False, methods=["get"])
    def search(self, request):
        """Search patients by name, email, or phone."""
        try:
            query = request.query_params.get("q", "").strip()

            if not query or len(query) < 2:
                return self.error_response(
                    "Search query must be at least 2 characters",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Get patients who have appointments with this doctor
            patients = User.objects.filter(
                patient_appointments__doctor=request.user
            ).distinct()

            # Filter by search query
            from django.db.models import Q

            patients = patients.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
                | Q(userprofile__phone__icontains=query)
            )

            patients_data = []
            for patient in patients[:20]:  # Limit to 20 results

                patient_profile = patient.userprofile

                patients_data.append(
                    {
                        "id": patient.id,
                        "name": patient.get_full_name(),
                        "email": patient.email,
                        "phone": patient_profile.phone,
                        "last_visit": self._get_last_visit(patient, request.user),
                    }
                )

            return self.success_response(
                data={
                    "patients": patients_data,
                    "query": query,
                    "total_found": len(patients_data),
                }
            )

        except Exception as e:
            return self.handle_exception(e, "Search failed")

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        """Get patient's medical timeline with this doctor."""
        try:
            patient = User.objects.get(id=pk)

            # Verify access
            if not Appointment.objects.filter(
                doctor=request.user, patient=patient
            ).exists():
                return self.error_response(
                    "Patient not found", status_code=status.HTTP_404_NOT_FOUND
                )

            # Get all appointments and medical records
            appointments = Appointment.objects.filter(
                doctor=request.user, patient=patient
            ).order_by("-appointment_date", "-start_time")

            timeline_data = []
            for apt in appointments:
                event = {
                    "id": apt.id,
                    "type": "appointment",
                    "date": apt.appointment_date.strftime("%Y-%m-%d"),
                    "time": apt.start_time.strftime("%I:%M %p"),
                    "appointment_type": apt.get_appointment_type_display(),
                    "status": apt.status,
                    "notes": apt.patient_notes,
                }

                # Add medical record if exists
                if hasattr(apt, "medical_record"):
                    record = apt.medical_record
                    event.update(
                        {
                            "has_medical_record": True,
                            "diagnosis": record.diagnosis,
                            "treatment": record.treatment,
                            "vitals": {
                                "blood_pressure": record.blood_pressure,
                                "heart_rate": record.heart_rate,
                                "temperature": (
                                    str(record.temperature)
                                    if record.temperature
                                    else None
                                ),
                                "weight": str(record.weight) if record.weight else None,
                            },
                        }
                    )
                else:
                    event["has_medical_record"] = False

                timeline_data.append(event)

            return self.success_response(
                data={
                    "patient_name": patient.get_full_name(),
                    "timeline": timeline_data,
                }
            )

        except User.DoesNotExist:
            return self.error_response(
                "Patient not found", status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return self.handle_exception(e, "Unable to load patient timeline")

    def _get_last_visit(self, patient, doctor):
        """Get last visit date for patient with doctor."""

        last_appointment = (
            Appointment.objects.filter(
                doctor=doctor, patient=patient, status="completed"
            )
            .order_by("-appointment_date")
            .first()
        )

        return (
            last_appointment.appointment_date.strftime("%Y-%m-%d")
            if last_appointment
            else None
        )
