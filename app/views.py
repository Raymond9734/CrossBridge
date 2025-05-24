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

    return inertia_render(request, "Index", props=dashboard_data)


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

    # Format medical records
    records_data = []
    for record in recent_records:
        records_data.append(
            {
                "id": record.id,
                "title": (
                    record.diagnosis[:50] + "..."
                    if len(record.diagnosis) > 50
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

    # Get recent patients
    recent_patients = (
        User.objects.filter(
            patient_appointments__doctor=user, patient_appointments__status="completed"
        )
        .distinct()
        .select_related("userprofile")[:5]
    )

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

    # Format recent patients
    patients_data = []
    for patient in recent_patients:
        last_appointment = (
            Appointment.objects.filter(patient=patient, doctor=user, status="completed")
            .order_by("-appointment_date")
            .first()
        )

        patients_data.append(
            {
                "id": patient.id,
                "name": patient.get_full_name(),
                "age": patient.userprofile.age or "N/A",
                "last_visit": (
                    last_appointment.appointment_date.strftime("%Y-%m-%d")
                    if last_appointment
                    else "N/A"
                ),
            }
        )

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
    }


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
        except Exception as e:
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

            except Exception as e:
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

        except Exception as e:
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

        except Exception as e:
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

    except Exception as e:
        return JsonResponse({"slots": []})


def about(request):
    """About page with loading indicator demo"""
    from time import sleep

    sleep(1)  # Reduced from 2.5 seconds for better UX
    return inertia_render(request, "About", props={"pageName": "About"})
