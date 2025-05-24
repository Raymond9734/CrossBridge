from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from django.utils import timezone
from django.db.models import Q
from inertia import render as inertia_render
from datetime import datetime, timedelta
import json
from .models import (
    UserProfile,
    DoctorAvailability,
    Appointment,
    MedicalRecord,
    Notification,
)
from django.db import models


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

            if user is not None:
                if user.is_active:
                    login(request, user)

                    # Set session expiry
                    if not remember:
                        request.session.set_expiry(0)
                    else:
                        request.session.set_expiry(1209600)  # 2 weeks

                    return redirect("index")
                else:
                    return inertia_render(
                        request,
                        "Login",
                        props={"errors": {"general": "Your account has been disabled"}},
                    )
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
        return redirect("index")

    return inertia_render(request, "Login", props={})


def register_view(request):
    """Handle registration page and user creation"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)

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

            # Create user
            try:
                # Create unique username from email
                username = email.split("@")[0]
                counter = 1
                original_username = username

                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1

                # Create the user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )

                # Update user profile
                user_profile = user.userprofile
                user_profile.role = role
                user_profile.phone = phone
                user_profile.save()

                # Auto-login
                login(request, user)
                return redirect("index")

            except Exception:
                return inertia_render(
                    request,
                    "Register",
                    props={
                        "errors": {
                            "general": "An error occurred while creating your account. Please try again."
                        },
                        "old": data,
                    },
                )

        except json.JSONDecodeError:
            return inertia_render(
                request,
                "Register",
                props={"errors": {"general": "Invalid request format"}},
            )

    if request.user.is_authenticated:
        return redirect("index")

    return inertia_render(request, "Register", props={})


def logout_view(request):
    """Handle user logout"""
    logout(request)
    return redirect("login")


@login_required
def profile_view(request):
    """Handle profile management"""
    user_profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Update user fields
            request.user.first_name = data.get("firstName", request.user.first_name)
            request.user.last_name = data.get("lastName", request.user.last_name)
            request.user.email = data.get("email", request.user.email)
            request.user.save()

            # Update profile fields
            user_profile.phone = data.get("phone", user_profile.phone)
            user_profile.address = data.get("address", user_profile.address)
            user_profile.emergency_contact = data.get(
                "emergencyContact", user_profile.emergency_contact
            )

            if user_profile.role == "patient":
                user_profile.medical_history = data.get(
                    "medicalHistory", user_profile.medical_history
                )

            user_profile.save()

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
def appointments_list_view(request):
    """List appointments for current user"""
    user_profile = get_object_or_404(UserProfile, user=request.user)

    # Filter appointments based on role
    if user_profile.role == "doctor":
        appointments = Appointment.objects.filter(doctor=request.user)
    else:
        appointments = Appointment.objects.filter(patient=request.user)

    # Apply additional filters
    status_filter = request.GET.get("status", "all")
    if status_filter != "all":
        appointments = appointments.filter(status=status_filter)

    search = request.GET.get("search", "")
    if search:
        if user_profile.role == "doctor":
            appointments = appointments.filter(
                Q(patient__first_name__icontains=search)
                | Q(patient__last_name__icontains=search)
            )
        else:
            appointments = appointments.filter(
                Q(doctor__first_name__icontains=search)
                | Q(doctor__last_name__icontains=search)
            )

    appointments = appointments.select_related("patient", "doctor").order_by(
        "-appointment_date", "-start_time"
    )

    # Format for frontend
    appointments_data = []
    for apt in appointments:
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
            "appointments": appointments_data,
            "userRole": user_profile.role,
            "filters": {"status": status_filter, "search": search},
        },
    )


@login_required
def book_appointment_view(request):
    """Handle appointment booking"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            doctor_name = data.get("doctor")
            appointment_date = data.get("date")
            appointment_time = data.get("time")
            appointment_type = data.get("type")
            notes = data.get("notes", "")

            # Validation
            errors = {}
            if not doctor_name:
                errors["doctor"] = "Please select a doctor"
            if not appointment_date:
                errors["date"] = "Please select a date"
            if not appointment_time:
                errors["time"] = "Please select a time"
            if not appointment_type:
                errors["type"] = "Please select appointment type"

            if errors:
                return JsonResponse({"success": False, "errors": errors})

            # Find doctor
            try:
                doctor_user = User.objects.get(
                    Q(first_name__icontains=doctor_name.replace("Dr. ", ""))
                    | Q(last_name__icontains=doctor_name.replace("Dr. ", ""))
                )
            except User.DoesNotExist:
                return JsonResponse(
                    {"success": False, "errors": {"doctor": "Doctor not found"}}
                )

            # Parse date and time
            try:
                apt_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
                apt_time = datetime.strptime(appointment_time, "%I:%M %p").time()
                # Assume 30-minute slots
                end_time = (
                    datetime.combine(apt_date, apt_time) + timedelta(minutes=30)
                ).time()
            except ValueError:
                return JsonResponse(
                    {
                        "success": False,
                        "errors": {"general": "Invalid date or time format"},
                    }
                )

            # Map frontend types to model choices
            type_mapping = {
                "Consultation": "consultation",
                "Follow-up": "follow_up",
                "Checkup": "checkup",
                "Emergency": "emergency",
            }

            # Create appointment
            appointment = Appointment.objects.create(
                patient=request.user,
                doctor=doctor_user,
                appointment_date=apt_date,
                start_time=apt_time,
                end_time=end_time,
                appointment_type=type_mapping.get(appointment_type, "consultation"),
                patient_notes=notes,
                status="pending",
                created_by=request.user,
            )

            # Create notification for doctor
            Notification.objects.create(
                user=doctor_user,
                notification_type="appointment_confirmed",
                title="New Appointment Request",
                message=f"{request.user.get_full_name()} has requested an appointment on {apt_date}",
                appointment=appointment,
            )

            return JsonResponse(
                {"success": True, "message": "Appointment booked successfully!"}
            )

        except Exception:
            return JsonResponse(
                {"success": False, "errors": {"general": "Failed to book appointment"}}
            )

    return JsonResponse(
        {"success": False, "errors": {"general": "Invalid request method"}}
    )


@login_required
def get_available_doctors(request):
    """Get list of available doctors"""
    doctors = User.objects.filter(
        userprofile__role="doctor", userprofile__doctorprofile__is_available=True
    ).select_related("userprofile__doctorprofile")

    doctors_data = []
    for doctor in doctors:
        doctor_profile = doctor.userprofile.doctorprofile
        doctors_data.append(
            {
                "id": doctor.id,
                "name": f"Dr. {doctor.get_full_name()}",
                "specialty": doctor_profile.specialty,
                "rating": float(doctor_profile.rating),
                "available": doctor_profile.is_available,
            }
        )

    return JsonResponse({"doctors": doctors_data})


@login_required
def get_available_slots(request):
    """Get available time slots for a doctor on a specific date"""
    doctor_id = request.GET.get("doctor_id")
    date_str = request.GET.get("date")

    if not doctor_id or not date_str:
        return JsonResponse({"slots": []})

    try:
        apt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        doctor = User.objects.get(id=doctor_id)

        # Get day of week (0=Monday, 6=Sunday)
        day_of_week = apt_date.weekday()

        # Get doctor's availability for this day
        availability = DoctorAvailability.objects.filter(
            doctor__user_profile__user=doctor,
            day_of_week=day_of_week,
            is_available=True,
        ).first()

        if not availability:
            return JsonResponse({"slots": []})

        # Generate time slots (30-minute intervals)
        slots = []
        current_time = availability.start_time
        end_time = availability.end_time

        while current_time < end_time:
            # Check if slot is already booked
            slot_end = (
                datetime.combine(apt_date, current_time) + timedelta(minutes=30)
            ).time()

            is_booked = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=apt_date,
                start_time=current_time,
                status__in=["pending", "confirmed", "in_progress"],
            ).exists()

            if not is_booked:
                slots.append(current_time.strftime("%I:%M %p"))

            # Move to next 30-minute slot
            current_time = (
                datetime.combine(apt_date, current_time) + timedelta(minutes=30)
            ).time()

        return JsonResponse({"slots": slots})

    except Exception:
        return JsonResponse({"slots": []})


def get_patient_dashboard_data(user):
    """Get dashboard data for patients"""
    # Get upcoming appointments
    upcoming_appointments = (
        Appointment.objects.filter(
            patient=user,
            appointment_date__gte=timezone.now().date(),
            status__in=["pending", "confirmed"],
        )
        .select_related("doctor", "doctor__userprofile")
        .order_by("appointment_date", "start_time")[:5]
    )

    # Get recent medical records
    recent_records = (
        MedicalRecord.objects.filter(appointment__patient=user)
        .select_related("appointment", "appointment__doctor")
        .order_by("-created_at")[:5]
    )

    # Format appointments for frontend
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

    # Format medical records for the medical records component
    medical_records_data = []
    for record in recent_records:
        medical_records_data.append(
            {
                "id": record.id,
                "date": record.created_at.isoformat(),
                "doctor_name": f"Dr. {record.appointment.doctor.get_full_name()}",
                "appointment_type": record.appointment.get_appointment_type_display(),
                "diagnosis": record.diagnosis,
                "treatment": record.treatment,
                "prescription": record.prescription,
                "lab_results": record.lab_results,
                "follow_up_required": record.follow_up_required,
                "follow_up_date": (
                    record.follow_up_date.isoformat() if record.follow_up_date else None
                ),
                "blood_pressure": (
                    f"{record.blood_pressure_systolic}/{record.blood_pressure_diastolic}"
                    if record.blood_pressure_systolic
                    and record.blood_pressure_diastolic
                    else None
                ),
                "heart_rate": record.heart_rate,
                "temperature": str(record.temperature) if record.temperature else None,
                "weight": str(record.weight) if record.weight else None,
            }
        )

    # Format simplified medical records for dashboard
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
                "doctor": f"Dr. {record.appointment.doctor.get_full_name()}",
                "date": record.created_at.strftime("%B %d, %Y"),
            }
        )

    # Get statistics
    total_appointments = Appointment.objects.filter(patient=user).count()
    completed_appointments = Appointment.objects.filter(
        patient=user, status="completed"
    ).count()
    pending_appointments = upcoming_appointments.count()

    return {
        "user": {
            "id": user.id,
            "name": user.get_full_name(),
            "email": user.email,
            "role": "patient",
        },
        "stats": {
            "upcoming_appointments": pending_appointments,
            "completed_visits": completed_appointments,
            "total_appointments": total_appointments,
        },
        "appointments": appointments_data,
        "medical_records": records_data,
        "medical_records_detailed": medical_records_data,  # For the medical records component
    }


def get_doctor_dashboard_data(user):
    """Get dashboard data for doctors"""
    today = timezone.now().date()

    # Get today's appointments
    todays_appointments = (
        Appointment.objects.filter(
            doctor=user,
            appointment_date=today,
            status__in=["pending", "confirmed", "in_progress"],
        )
        .select_related("patient", "patient__userprofile")
        .order_by("start_time")
    )

    # Get recent patients with more details
    recent_patients_query = (
        Appointment.objects.filter(doctor=user, status="completed")
        .values("patient")
        .annotate(
            last_appointment_date=models.Max("appointment_date"),
            total_appointments=models.Count("id"),
        )
        .order_by("-last_appointment_date")[:10]
    )

    # Get detailed patient information
    patients_data = []
    for patient_data in recent_patients_query:
        try:
            patient = User.objects.get(id=patient_data["patient"])
            patient_profile = patient.userprofile

            patients_data.append(
                {
                    "id": patient.id,
                    "name": patient.get_full_name(),
                    "email": patient.email,
                    "phone": patient_profile.phone,
                    "age": patient_profile.age,
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
                    "last_visit": (
                        patient_data["last_appointment_date"].strftime("%Y-%m-%d")
                        if patient_data["last_appointment_date"]
                        else None
                    ),
                    "total_appointments": patient_data["total_appointments"],
                    "created_at": patient_profile.created_at.isoformat(),
                }
            )
        except User.DoesNotExist:
            continue

    # Format today's appointments
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

    # Get doctor availability (for schedule management)
    try:
        doctor_profile = user.userprofile.doctorprofile
        availability_data = []
        for avail in doctor_profile.availability.all():
            availability_data.append(
                {
                    "id": avail.id,
                    "day_of_week": avail.day_of_week,
                    "start_time": avail.start_time.strftime("%H:%M"),
                    "end_time": avail.end_time.strftime("%H:%M"),
                    "is_available": avail.is_available,
                }
            )
    except:
        availability_data = []

    # Get statistics
    todays_count = todays_appointments.count()
    total_patients = (
        User.objects.filter(patient_appointments__doctor=user).distinct().count()
    )
    pending_reviews = MedicalRecord.objects.filter(
        appointment__doctor=user, diagnosis=""
    ).count()

    return {
        "user": {
            "id": user.id,
            "name": user.get_full_name(),
            "email": user.email,
            "role": "doctor",
        },
        "stats": {
            "todays_appointments": todays_count,
            "total_patients": total_patients,
            "pending_reviews": pending_reviews,
        },
        "appointments": appointments_data,
        "patients": patients_data,
        "doctor_availability": availability_data,
    }


# Update the main index view
def index(request):
    """Main dashboard - redirects based on authentication"""
    if not request.user.is_authenticated:
        return redirect("login")

    # Get user profile and related data
    user_profile = get_object_or_404(UserProfile, user=request.user)

    # Prepare dashboard data based on user role
    if user_profile.role == "doctor":
        dashboard_data = get_doctor_dashboard_data(request.user)
    else:
        dashboard_data = get_patient_dashboard_data(request.user)

    notifications = Notification.objects.filter(
        user=request.user, is_read=False
    ).order_by("-created_at")[:10]

    notifications_data = {
        "unread_count": notifications.count(),
        "items": [
            {
                "id": notif.id,
                "type": notif.notification_type,
                "title": notif.title,
                "message": notif.message,
                "created_at": notif.created_at.isoformat(),
                "is_read": notif.is_read,
            }
            for notif in notifications
        ],
    }

    dashboard_data["notifications"] = notifications_data

    # Add the detailed medical records for the medical records component
    if user_profile.role == "patient":
        dashboard_data["medical_records"] = dashboard_data.get(
            "medical_records_detailed", []
        )

    return inertia_render(request, "Index", props=dashboard_data)


# Add new endpoints for the enhanced functionality
@login_required
def medical_records_view(request):
    """Get detailed medical records for patient"""
    user_profile = get_object_or_404(UserProfile, user=request.user)

    if user_profile.role != "patient":
        return JsonResponse({"error": "Access denied"}, status=403)

    # Get all medical records
    records = (
        MedicalRecord.objects.filter(appointment__patient=request.user)
        .select_related("appointment", "appointment__doctor")
        .order_by("-created_at")
    )

    records_data = []
    for record in records:
        records_data.append(
            {
                "id": record.id,
                "date": record.created_at.isoformat(),
                "doctor_name": f"Dr. {record.appointment.doctor.get_full_name()}",
                "appointment_type": record.appointment.get_appointment_type_display(),
                "diagnosis": record.diagnosis,
                "treatment": record.treatment,
                "prescription": record.prescription,
                "lab_results": record.lab_results,
                "follow_up_required": record.follow_up_required,
                "follow_up_date": (
                    record.follow_up_date.isoformat() if record.follow_up_date else None
                ),
                "blood_pressure": (
                    f"{record.blood_pressure_systolic}/{record.blood_pressure_diastolic}"
                    if record.blood_pressure_systolic
                    and record.blood_pressure_diastolic
                    else None
                ),
                "heart_rate": record.heart_rate,
                "temperature": str(record.temperature) if record.temperature else None,
                "weight": str(record.weight) if record.weight else None,
            }
        )

    return JsonResponse({"medical_records": records_data})


@login_required
def doctor_availability_view(request):
    """Get doctor availability for schedule management"""

    user_profile = get_object_or_404(UserProfile, user=request.user)

    if user_profile.role != "doctor":
        return JsonResponse({"error": "Access denied"}, status=403)

    doctor_profile = user_profile.doctorprofile
    availability_data = []
    for avail in doctor_profile.availability.all():
        availability_data.append(
            {
                "id": avail.id,
                "day_of_week": avail.day_of_week,
                "start_time": avail.start_time.strftime("%H:%M"),
                "end_time": avail.end_time.strftime("%H:%M"),
                "is_available": avail.is_available,
            }
        )

    return JsonResponse({"doctor_availability": availability_data})


@login_required
def patients_list_view(request):
    """Get patients list for doctor"""
    user_profile = get_object_or_404(UserProfile, user=request.user)

    if user_profile.role != "doctor":
        return JsonResponse({"error": "Access denied"}, status=403)

    # Get patients who have appointments with this doctor
    patients_query = (
        Appointment.objects.filter(doctor=request.user)
        .values("patient")
        .annotate(
            last_appointment_date=models.Max("appointment_date"),
            total_appointments=models.Count("id"),
        )
        .order_by("-last_appointment_date")
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
                    "age": patient_profile.age,
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
                    "last_visit": (
                        patient_data["last_appointment_date"].strftime("%Y-%m-%d")
                        if patient_data["last_appointment_date"]
                        else None
                    ),
                    "total_appointments": patient_data["total_appointments"],
                    "created_at": patient_profile.created_at.isoformat(),
                }
            )
        except User.DoesNotExist:
            continue

    return JsonResponse({"patients": patients_data})


# Add this to your views.py, replacing the existing doctor_availability_view


@login_required
def doctor_availability_view(request):
    """Handle doctor availability - GET, POST, PUT, DELETE"""
    user_profile = get_object_or_404(UserProfile, user=request.user)

    if user_profile.role != "doctor":
        return JsonResponse({"error": "Access denied"}, status=403)

    try:
        doctor_profile = user_profile.doctorprofile
    except:
        return JsonResponse({"error": "Doctor profile not found"}, status=404)

    if request.method == "GET":
        # Return existing availability
        availability_data = []
        for avail in doctor_profile.availability.all():
            availability_data.append(
                {
                    "id": avail.id,
                    "day_of_week": avail.day_of_week,
                    "start_time": avail.start_time.strftime("%H:%M"),
                    "end_time": avail.end_time.strftime("%H:%M"),
                    "is_available": avail.is_available,
                }
            )

        return JsonResponse({"doctor_availability": availability_data})

    elif request.method == "POST":
        # Create new availability slot
        try:
            data = json.loads(request.body)

            day_of_week = data.get("day_of_week")
            start_time = data.get("start_time")
            end_time = data.get("end_time")
            is_available = data.get("is_available", True)

            # Validation
            errors = {}
            if day_of_week is None or day_of_week == "":
                errors["day_of_week"] = "Day of week is required"
            elif not (0 <= int(day_of_week) <= 6):
                errors["day_of_week"] = "Invalid day of week"

            if not start_time:
                errors["start_time"] = "Start time is required"
            if not end_time:
                errors["end_time"] = "End time is required"

            # Parse and validate times
            try:
                from datetime import datetime, time

                start_time_obj = datetime.strptime(start_time, "%H:%M").time()
                end_time_obj = datetime.strptime(end_time, "%H:%M").time()

                if start_time_obj >= end_time_obj:
                    errors["end_time"] = "End time must be after start time"

            except ValueError:
                errors["time"] = "Invalid time format. Use HH:MM format"

            if errors:
                return JsonResponse({"success": False, "errors": errors}, status=400)

            # Check for overlapping availability on the same day
            overlapping = DoctorAvailability.objects.filter(
                doctor=doctor_profile, day_of_week=day_of_week
            )

            for existing in overlapping:
                if (
                    start_time_obj < existing.end_time
                    and end_time_obj > existing.start_time
                ):
                    return JsonResponse(
                        {
                            "success": False,
                            "errors": {
                                "general": "This time slot overlaps with existing availability"
                            },
                        },
                        status=400,
                    )

            # Create the availability slot
            availability = DoctorAvailability.objects.create(
                doctor=doctor_profile,
                day_of_week=int(day_of_week),
                start_time=start_time_obj,
                end_time=end_time_obj,
                is_available=is_available,
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Availability added successfully",
                    "availability": {
                        "id": availability.id,
                        "day_of_week": availability.day_of_week,
                        "start_time": availability.start_time.strftime("%H:%M"),
                        "end_time": availability.end_time.strftime("%H:%M"),
                        "is_available": availability.is_available,
                    },
                }
            )

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    elif request.method == "PUT":
        # Update existing availability slot
        try:
            data = json.loads(request.body)
            availability_id = data.get("id")

            if not availability_id:
                return JsonResponse(
                    {"success": False, "error": "Availability ID is required"},
                    status=400,
                )

            availability = get_object_or_404(
                DoctorAvailability, id=availability_id, doctor=doctor_profile
            )

            # Update fields if provided
            if "is_available" in data:
                availability.is_available = data["is_available"]

            if "start_time" in data and "end_time" in data:
                try:
                    start_time_obj = datetime.strptime(
                        data["start_time"], "%H:%M"
                    ).time()
                    end_time_obj = datetime.strptime(data["end_time"], "%H:%M").time()

                    if start_time_obj >= end_time_obj:
                        return JsonResponse(
                            {
                                "success": False,
                                "errors": {
                                    "end_time": "End time must be after start time"
                                },
                            },
                            status=400,
                        )

                    availability.start_time = start_time_obj
                    availability.end_time = end_time_obj

                except ValueError:
                    return JsonResponse(
                        {"success": False, "errors": {"time": "Invalid time format"}},
                        status=400,
                    )

            availability.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": "Availability updated successfully",
                    "availability": {
                        "id": availability.id,
                        "day_of_week": availability.day_of_week,
                        "start_time": availability.start_time.strftime("%H:%M"),
                        "end_time": availability.end_time.strftime("%H:%M"),
                        "is_available": availability.is_available,
                    },
                }
            )

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    elif request.method == "DELETE":
        # Delete availability slot
        try:
            data = json.loads(request.body)
            availability_id = data.get("id")

            if not availability_id:
                return JsonResponse(
                    {"success": False, "error": "Availability ID is required"},
                    status=400,
                )

            availability = get_object_or_404(
                DoctorAvailability, id=availability_id, doctor=doctor_profile
            )
            availability.delete()

            return JsonResponse(
                {"success": True, "message": "Availability deleted successfully"}
            )

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


@login_required
def toggle_availability_view(request):
    """Toggle availability status for a specific slot"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user_profile = get_object_or_404(UserProfile, user=request.user)
    if user_profile.role != "doctor":
        return JsonResponse({"error": "Access denied"}, status=403)

    try:
        doctor_profile = user_profile.doctorprofile
        data = json.loads(request.body)
        availability_id = data.get("id")

        if not availability_id:
            return JsonResponse(
                {"success": False, "error": "Availability ID is required"}, status=400
            )

        availability = get_object_or_404(
            DoctorAvailability, id=availability_id, doctor=doctor_profile
        )
        availability.is_available = not availability.is_available
        availability.save()

        return JsonResponse(
            {
                "success": True,
                "message": f"Availability {'enabled' if availability.is_available else 'disabled'}",
                "is_available": availability.is_available,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# Add a view to get day names for the frontend
@login_required
def get_days_of_week(request):
    """Get days of week for frontend dropdown"""
    days = [
        {"id": 0, "name": "Monday"},
        {"id": 1, "name": "Tuesday"},
        {"id": 2, "name": "Wednesday"},
        {"id": 3, "name": "Thursday"},
        {"id": 4, "name": "Friday"},
        {"id": 5, "name": "Saturday"},
        {"id": 6, "name": "Sunday"},
    ]
    return JsonResponse({"days": days})


@login_required
def cancel_appointment_view(request):
    """Cancel an appointment"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        appointment_id = data.get("appointment_id")

        if not appointment_id:
            return JsonResponse(
                {"success": False, "error": "Appointment ID is required"}, status=400
            )

        # Get appointment - ensure user has permission to cancel it
        appointment = get_object_or_404(
            Appointment.objects.filter(
                Q(patient=request.user) | Q(doctor=request.user)
            ),
            id=appointment_id,
        )

        # Check if appointment can be cancelled
        if appointment.status in ["completed", "cancelled"]:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Cannot cancel a completed or already cancelled appointment",
                },
                status=400,
            )

        # Update appointment status
        appointment.status = "cancelled"
        appointment.save()

        # Create notification for the other party
        if appointment.patient == request.user:
            # Patient cancelled, notify doctor
            other_user = appointment.doctor
            message = f"Patient {request.user.get_full_name()} has cancelled their appointment on {appointment.appointment_date}"
        else:
            # Doctor cancelled, notify patient
            other_user = appointment.patient
            message = f"Dr. {request.user.get_full_name()} has cancelled your appointment on {appointment.appointment_date}"

        Notification.objects.create(
            user=other_user,
            notification_type="appointment_cancelled",
            title="Appointment Cancelled",
            message=message,
            appointment=appointment,
        )

        return JsonResponse(
            {"success": True, "message": "Appointment cancelled successfully"}
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
