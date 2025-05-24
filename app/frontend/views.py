from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from inertia import render as inertia_render
from datetime import datetime
import json

# Import from modular apps
from app.account.models import UserProfile, DoctorProfile
from app.account.services import UserProfileService, DoctorProfileService
from app.appointment.models import Appointment
from app.appointment.services import AppointmentService, DoctorAvailabilityService
from app.medical_record.services import MedicalRecordService
from app.notification.services import NotificationService

# Log error and return minimal data
import logging

logger = logging.getLogger(__name__)


def login_view(request):
    """Handle login page and authentication"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email", "").strip()
            password = data.get("password")
            remember = data.get("remember", False)

            if not email or not password:
                return inertia_render(
                    request,
                    "Login",
                    props={"errors": {"general": "Email and password are required"}},
                )

            # Find user by email
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(
                    request, username=user_obj.username, password=password
                )
            except User.DoesNotExist:
                return inertia_render(
                    request,
                    "Login",
                    props={"errors": {"general": "Invalid email or password"}},
                )

            if user is not None and user.is_active:
                login(request, user)

                # Set session expiry
                if not remember:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)  # 2 weeks

                return redirect("frontend:index")
            else:
                return inertia_render(
                    request,
                    "Login",
                    props={"errors": {"general": "Invalid email or password"}},
                )

        except json.JSONDecodeError:
            return inertia_render(
                request,
                "Login",
                props={"errors": {"general": "Invalid request format"}},
            )
        except Exception:
            return inertia_render(
                request,
                "Login",
                props={"errors": {"general": "An error occurred. Please try again."}},
            )

    if request.user.is_authenticated:
        return redirect("frontend:index")

    return inertia_render(request, "Login", props={})


def register_view(request):
    """Handle registration page and user creation"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_service = UserProfileService()

            first_name = data.get("firstName", "").strip()
            last_name = data.get("lastName", "").strip()
            email = data.get("email", "").strip()
            phone = data.get("phone", "").strip()
            password = data.get("password")
            confirm_password = data.get("confirmPassword")
            role = data.get("role", "patient")
            terms = data.get("terms", False)

            # Server-side validation
            errors = {}

            if not first_name:
                errors["firstName"] = "First name is required"
            if not last_name:
                errors["lastName"] = "Last name is required"
            if not email:
                errors["email"] = "Email is required"
            elif User.objects.filter(email=email).exists():
                errors["email"] = "An account with this email already exists"
            if not phone:
                errors["phone"] = "Phone number is required"
            if not password:
                errors["password"] = "Password is required"
            elif len(password) < 8:
                errors["password"] = "Password must be at least 8 characters"
            if password != confirm_password:
                errors["confirmPassword"] = "Passwords do not match"
            if not terms:
                errors["terms"] = "You must accept the terms and conditions"
            if role not in ["patient", "doctor"]:
                errors["role"] = "Invalid role selection"

            if errors:
                return inertia_render(
                    request, "Register", props={"errors": errors, "old": data}
                )

            # Create user using service
            user_data = {
                "email": email,
                "password": password,
                "first_name": first_name,
                "last_name": last_name,
            }

            profile_data = {
                "phone": phone,
            }

            if role == "doctor":
                doctor_data = {
                    "specialty": "General Medicine",  # Default
                    "license_number": f"LIC-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                }
                profile = user_service.create_doctor_profile(
                    user_data, profile_data, doctor_data
                )
            else:
                profile = user_service.create_patient_profile(user_data, profile_data)

            # Auto-login
            login(request, profile.user)
            return redirect("frontend:index")

        except Exception as e:
            logger.error(f"Error during registration: {e}")
            return inertia_render(
                request,
                "Register",
                props={
                    "errors": {
                        "general": "An error occurred while creating your account. Please try again."
                    },
                    "old": data if "data" in locals() else {},
                },
            )

    if request.user.is_authenticated:
        return redirect("frontend:index")

    return inertia_render(request, "Register", props={})


def forgot_password_view(request):
    """Handle forgot password page"""
    if request.method == "POST":
        # TODO: Implement password reset logic
        return inertia_render(
            request,
            "ForgotPassword",
            props={"message": "Password reset functionality coming soon"},
        )

    return inertia_render(request, "ForgotPassword", props={})


def logout_view(request):
    """Handle user logout"""
    logout(request)
    return redirect("frontend:login")


@login_required
def index(request):
    """Main dashboard - redirects based on authentication"""
    return dashboard_view(request)


@login_required
def dashboard_view(request):
    """Dashboard with role-specific data"""
    try:
        user_profile = get_object_or_404(UserProfile, user=request.user)

        # Get dashboard data based on role
        if user_profile.role == "doctor":
            dashboard_data = _get_doctor_dashboard_data(request.user)
        else:
            dashboard_data = _get_patient_dashboard_data(request.user)

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

        return inertia_render(request, "Index", props=dashboard_data)

    except Exception as e:

        logger.error(f"Dashboard error for user {request.user.id}: {e}")

        return inertia_render(
            request,
            "Index",
            props={
                "user": {"name": request.user.get_full_name(), "role": "patient"},
                "error": "Unable to load dashboard data",
            },
        )


@login_required
def appointments_view(request):
    """Appointments page"""
    appointment_service = AppointmentService()
    user_profile = get_object_or_404(UserProfile, user=request.user)

    try:
        if user_profile.role == "doctor":
            appointments = appointment_service.get_doctor_appointments(request.user)
        else:
            appointments = appointment_service.get_patient_appointments(request.user)

        appointments_data = []
        for apt in appointments[:50]:  # Limit to 50 most recent
            appointments_data.append(
                {
                    "id": apt.id,
                    "patient": apt.patient.get_full_name(),
                    "doctor": f"Dr. {apt.doctor.get_full_name()}",
                    "date": apt.appointment_date.strftime("%Y-%m-%d"),
                    "time": apt.start_time.strftime("%I:%M %p"),
                    "type": apt.get_appointment_type_display(),
                    "status": apt.status,
                }
            )

        return inertia_render(
            request,
            "Appointments",
            props={
                "appointments_list": appointments_data,
                "user_role": user_profile.role,
            },
        )

    except Exception:
        return inertia_render(
            request,
            "Appointments",
            props={"appointments_list": [], "error": "Unable to load appointments"},
        )


@login_required
def medical_records_view(request):
    """Medical records page"""
    medical_record_service = MedicalRecordService()
    user_profile = get_object_or_404(UserProfile, user=request.user)

    if user_profile.role != "patient":
        return redirect("frontend:index")

    try:
        records = medical_record_service.get_patient_records(request.user, limit=50)

        records_data = []
        for record in records:
            records_data.append(
                {
                    "id": record.id,
                    "date": record.created_at.isoformat(),
                    "doctor_name": f"Dr. {record.doctor.get_full_name()}",
                    "appointment_type": record.appointment.get_appointment_type_display(),
                    "diagnosis": record.diagnosis,
                    "treatment": record.treatment,
                    "prescription": record.prescription,
                    "follow_up_required": record.follow_up_required,
                    "follow_up_date": (
                        record.follow_up_date.isoformat()
                        if record.follow_up_date
                        else None
                    ),
                    "blood_pressure": record.blood_pressure,
                    "heart_rate": record.heart_rate,
                    "temperature": (
                        str(record.temperature) if record.temperature else None
                    ),
                    "weight": str(record.weight) if record.weight else None,
                }
            )

        return inertia_render(
            request, "MedicalRecords", props={"medical_records": records_data}
        )

    except Exception:
        return inertia_render(
            request,
            "MedicalRecords",
            props={"medical_records": [], "error": "Unable to load medical records"},
        )


@login_required
def profile_view(request):
    """Profile management page"""
    user_profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_service = UserProfileService()

            # Update profile
            user_service.update_profile(user_profile, data)

            return JsonResponse(
                {"success": True, "message": "Profile updated successfully"}
            )
        except Exception:
            return JsonResponse({"success": False, "error": "Failed to update profile"})

    # GET request - return current profile data
    profile_data = {
        "firstName": request.user.first_name,
        "lastName": request.user.last_name,
        "email": request.user.email,
        "phone": user_profile.phone,
        "address": user_profile.address,
        "emergencyContact": user_profile.emergency_contact,
        "emergencyPhone": user_profile.emergency_phone,
        "medicalHistory": (
            user_profile.medical_history if user_profile.role == "patient" else ""
        ),
        "role": user_profile.role,
    }

    return inertia_render(
        request,
        "Profile",
        props={
            "profile": profile_data,
            "user": {
                "id": request.user.id,
                "name": request.user.get_full_name(),
                "email": request.user.email,
                "role": user_profile.role,
            },
        },
    )


@login_required
def schedule_view(request):
    """Doctor schedule management page"""
    user_profile = get_object_or_404(UserProfile, user=request.user)

    if user_profile.role != "doctor":
        return redirect("frontend:index")

    try:
        doctor_profile = user_profile.doctorprofile
        availability_service = DoctorAvailabilityService()

        availability_data = []
        for avail in availability_service.get_doctor_availability(doctor_profile):
            availability_data.append(
                {
                    "id": avail.id,
                    "day_of_week": avail.day_of_week,
                    "start_time": avail.start_time.strftime("%H:%M"),
                    "end_time": avail.end_time.strftime("%H:%M"),
                    "is_available": avail.is_available,
                }
            )

        return inertia_render(
            request,
            "Schedule",
            props={"doctor_availability": availability_data},
        )

    except Exception:
        return inertia_render(
            request,
            "Schedule",
            props={"doctor_availability": [], "error": "Unable to load schedule"},
        )


@login_required
def patients_view(request):
    """Doctor patients management page"""
    user_profile = get_object_or_404(UserProfile, user=request.user)

    if user_profile.role != "doctor":
        return redirect("frontend:index")

    try:
        # doctor_service = DoctorProfileService()

        # Get patients who have appointments with this doctor
        patients_query = (
            Appointment.objects.filter(doctor=request.user).values("patient").distinct()
        )

        patients_data = []
        for patient_data in patients_query:
            try:
                patient = User.objects.get(id=patient_data["patient"])
                patient_profile = patient.userprofile

                patients_data.append(
                    {
                        "id": patient.id,
                        "name": patient.get_full_name(),
                        "email": patient.email,
                        "phone": patient_profile.phone,
                        "date_of_birth": (
                            patient_profile.date_of_birth.isoformat()
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
                        "created_at": patient_profile.created_at.isoformat(),
                    }
                )
            except User.DoesNotExist:
                continue

        return inertia_render(
            request,
            "Patients",
            props={"patients": patients_data},
        )

    except Exception:
        return inertia_render(
            request,
            "Patients",
            props={"patients": [], "error": "Unable to load patients"},
        )


# AJAX endpoints for frontend functionality
@login_required
def book_appointment_ajax(request):
    """Handle appointment booking via AJAX"""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"})

    try:
        data = json.loads(request.body)
        appointment_service = AppointmentService()

        doctor_name = data.get("doctor")
        appointment_date = data.get("date")
        appointment_time = data.get("time")
        appointment_type = data.get("type")
        notes = data.get("notes", "")

        # Find doctor
        try:
            # Extract name from "Dr. FirstName LastName" format
            name_parts = doctor_name.replace("Dr. ", "").split()
            if len(name_parts) >= 2:
                first_name, last_name = name_parts[0], name_parts[1]
                doctor_user = User.objects.get(
                    first_name__icontains=first_name,
                    last_name__icontains=last_name,
                    userprofile__role="doctor",
                )
            else:
                return JsonResponse(
                    {"success": False, "error": "Invalid doctor name format"}
                )
        except User.DoesNotExist:
            return JsonResponse({"success": False, "error": "Doctor not found"})

        # Parse date and time
        try:
            apt_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
            apt_time = datetime.strptime(appointment_time, "%I:%M %p").time()
        except ValueError:
            return JsonResponse(
                {"success": False, "error": "Invalid date or time format"}
            )

        # Map frontend types to model choices
        type_mapping = {
            "Consultation": "consultation",
            "Follow-up": "follow_up",
            "Checkup": "checkup",
            "Emergency": "emergency",
        }

        # Book appointment using service
        appointment_service.book_appointment(
            patient=request.user,
            doctor_id=doctor_user.id,
            appointment_date=apt_date,
            start_time=apt_time,
            appointment_type=type_mapping.get(appointment_type, "consultation"),
            patient_notes=notes,
        )

        return JsonResponse(
            {"success": True, "message": "Appointment booked successfully!"}
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
def get_available_doctors_ajax(request):
    """Get list of available doctors via AJAX"""
    try:
        # doctor_service = DoctorProfileService()
        specialty = request.GET.get("specialty")

        doctors = DoctorProfile.objects.filter(
            is_available=True, accepts_new_patients=True
        )
        if specialty:
            doctors = doctors.filter(specialty__icontains=specialty)

        doctors_data = []
        for doctor_profile in doctors.select_related("user_profile__user"):
            doctors_data.append(
                {
                    "id": doctor_profile.user_profile.user.id,
                    "name": f"Dr. {doctor_profile.user_profile.user.get_full_name()}",
                    "specialty": doctor_profile.specialty,
                    "rating": float(doctor_profile.rating),
                    "available": doctor_profile.is_available,
                }
            )

        return JsonResponse({"doctors": doctors_data})
    except Exception:
        return JsonResponse({"doctors": []})


@login_required
def get_available_slots_ajax(request):
    """Get available time slots for a doctor on a specific date via AJAX"""
    try:
        doctor_id = request.GET.get("doctor_id")
        date_str = request.GET.get("date")

        if not doctor_id or not date_str:
            return JsonResponse({"slots": []})

        apt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        doctor = User.objects.get(id=doctor_id)

        appointment_service = AppointmentService()
        slots = appointment_service.get_available_slots(doctor, apt_date)

        return JsonResponse({"slots": [slot.strftime("%I:%M %p") for slot in slots]})

    except Exception:
        return JsonResponse({"slots": []})


# Helper functions
def _get_patient_dashboard_data(user):
    """Get dashboard data for patients"""

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


def _get_doctor_dashboard_data(user):
    """Get dashboard data for doctors"""
    appointment_service = AppointmentService()
    doctor_service = DoctorProfileService()
    today = timezone.now().date()

    # Get today's appointments
    todays_appointments = appointment_service.get_doctor_appointments(user, date=today)

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
        "patients": [],  # Will be loaded on patients page
    }
