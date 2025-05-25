from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.contrib.auth.models import User
from django.core.cache import cache
from datetime import datetime, timedelta
from django.utils import timezone
import logging

from app.appointment.services import AppointmentService
from app.account.models import DoctorProfile
from django.views.decorators.cache import never_cache
from django.core.cache import cache as django_cache

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@cache_page(60 * 5)  # Cache for 5 minutes
def get_available_slots_ajax(request):
    """Get available time slots for AJAX requests (matches frontend expectations)."""
    try:
        doctor_id = request.GET.get("doctor_id")
        date_str = request.GET.get("date")

        # Validate required parameters
        if not doctor_id or not date_str:
            return JsonResponse(
                {
                    "success": False,
                    "slots": [],
                    "error": "Missing required parameters: doctor_id and date",
                }
            )

        # Validate doctor_id is numeric
        try:
            doctor_id = int(doctor_id)
        except (ValueError, TypeError):
            return JsonResponse(
                {"success": False, "slots": [], "error": "Invalid doctor_id format"}
            )

        # Parse and validate date
        try:
            apt_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Don't allow dates in the past
            if apt_date < timezone.now().date():
                return JsonResponse(
                    {
                        "success": False,
                        "slots": [],
                        "error": "Cannot get slots for past dates",
                    }
                )

            # Don't allow dates too far in the future (e.g., more than 3 months)
            max_future_date = timezone.now().date() + timedelta(days=90)
            if apt_date > max_future_date:
                return JsonResponse(
                    {
                        "success": False,
                        "slots": [],
                        "error": "Cannot get slots more than 3 months in advance",
                    }
                )

        except ValueError:
            return JsonResponse(
                {
                    "success": False,
                    "slots": [],
                    "error": "Invalid date format. Use YYYY-MM-DD",
                }
            )

        # Get doctor and validate
        try:
            doctor = User.objects.select_related("userprofile").get(
                id=doctor_id, userprofile__role="doctor"
            )

            # Check if doctor is available
            doctor_profile = getattr(doctor.userprofile, "doctorprofile", None)
            if not doctor_profile or not doctor_profile.is_available:
                return JsonResponse(
                    {"success": False, "slots": [], "error": "Doctor is not available"}
                )

        except User.DoesNotExist:
            return JsonResponse(
                {"success": False, "slots": [], "error": "Doctor not found"}
            )

        # Check cache first
        cache_key = f"available_slots:{doctor_id}:{date_str}"
        cached_slots = cache.get(cache_key)

        if cached_slots is not None:
            return JsonResponse(
                {"success": True, "slots": cached_slots, "cached": True}
            )

        # Get available slots using service
        appointment_service = AppointmentService()
        slots = appointment_service.get_available_slots(doctor, apt_date)

        # Format slots for frontend
        formatted_slots = [slot.strftime("%I:%M %p") for slot in slots]

        # Cache the result for 5 minutes
        cache.set(cache_key, formatted_slots, 300)

        return JsonResponse(
            {
                "success": True,
                "slots": formatted_slots,
                "date": date_str,
                "doctor_name": f"Dr. {doctor.get_full_name()}",
                "cached": False,
            }
        )

    except Exception as e:
        logger.error(f"Available slots error for doctor {doctor_id} on {date_str}: {e}")
        return JsonResponse(
            {
                "success": False,
                "slots": [],
                "error": "An error occurred while fetching available slots",
            }
        )


@require_http_methods(["GET"])
@cache_page(60 * 10)  # Cache for 10 minutes
def get_available_doctors_ajax(request):
    """Get available doctors for AJAX requests (matches frontend expectations)."""
    try:
        specialty = request.GET.get("specialty")
        limit = request.GET.get("limit", "20")  # Default limit of 20

        # Validate limit parameter
        try:
            limit = int(limit)
            if limit > 100:  # Cap at 100 to prevent abuse
                limit = 100
        except (ValueError, TypeError):
            limit = 20

        # Check cache first
        cache_key = f"available_doctors:{specialty or 'all'}:{limit}"
        cached_doctors = cache.get(cache_key)

        if cached_doctors is not None:
            return JsonResponse(
                {"success": True, "doctors": cached_doctors, "cached": True}
            )

        # Build queryset
        queryset = DoctorProfile.objects.filter(
            is_available=True, accepts_new_patients=True
        ).select_related("user_profile__user")

        # Apply specialty filter if provided
        if specialty and specialty.strip():
            queryset = queryset.filter(specialty__icontains=specialty.strip())

        # Order by rating (highest first) and then by name
        queryset = queryset.order_by("-rating", "user_profile__user__first_name")

        # Apply limit
        queryset = queryset[:limit]

        # Build response data
        doctors = []
        for doctor_profile in queryset:
            user = doctor_profile.user_profile.user

            # Get consultation fee
            consultation_fee = None
            if doctor_profile.consultation_fee:
                consultation_fee = float(doctor_profile.consultation_fee)

            doctors.append(
                {
                    "id": user.id,
                    "name": f"Dr. {user.get_full_name()}",
                    "specialty": doctor_profile.specialty,
                    "subspecialty": doctor_profile.subspecialty or "",
                    "rating": float(doctor_profile.rating),
                    "total_reviews": doctor_profile.total_reviews,
                    "years_experience": doctor_profile.years_experience,
                    "consultation_fee": consultation_fee,
                    "available": doctor_profile.is_available,
                    "accepts_new_patients": doctor_profile.accepts_new_patients,
                    "hospital_affiliation": doctor_profile.hospital_affiliation or "",
                    "bio": (
                        doctor_profile.bio[:200] + "..."
                        if len(doctor_profile.bio) > 200
                        else doctor_profile.bio
                    ),
                }
            )

        # Cache the result for 10 minutes
        cache.set(cache_key, doctors, 600)

        return JsonResponse(
            {
                "success": True,
                "doctors": doctors,
                "count": len(doctors),
                "specialty_filter": specialty,
                "cached": False,
            }
        )

    except Exception as e:
        logger.error(f"Available doctors error: {e}")
        return JsonResponse(
            {
                "success": False,
                "doctors": [],
                "error": "An error occurred while fetching available doctors",
            }
        )


# Additional utility function for getting doctor specialties
@require_http_methods(["GET"])
@cache_page(60 * 30)  # Cache for 30 minutes
def get_specialties_ajax(request):
    """Get list of available specialties for filtering."""
    try:
        cache_key = "doctor_specialties"
        cached_specialties = cache.get(cache_key)

        if cached_specialties is not None:
            return JsonResponse(
                {"success": True, "specialties": cached_specialties, "cached": True}
            )

        # Get unique specialties from available doctors
        specialties = (
            DoctorProfile.objects.filter(is_available=True, accepts_new_patients=True)
            .values_list("specialty", flat=True)
            .distinct()
            .order_by("specialty")
        )

        specialty_list = [specialty for specialty in specialties if specialty]

        # Cache for 30 minutes
        cache.set(cache_key, specialty_list, 1800)

        return JsonResponse(
            {
                "success": True,
                "specialties": specialty_list,
                "count": len(specialty_list),
                "cached": False,
            }
        )

    except Exception as e:
        logger.error(f"Get specialties error: {e}")
        return JsonResponse(
            {
                "success": False,
                "specialties": [],
                "error": "An error occurred while fetching specialties",
            }
        )


# Rate-limited version for appointment booking


@require_http_methods(["POST"])
@never_cache
def book_appointment_ajax(request):
    """Book appointment via AJAX with rate limiting."""
    try:
        # Simple rate limiting
        user_key = f"book_appointment_rate:{request.user.id if request.user.is_authenticated else request.META.get('REMOTE_ADDR')}"

        # Check if user has made a booking request in the last minute
        if django_cache.get(user_key):
            return JsonResponse(
                {
                    "success": False,
                    "error": "Please wait before making another booking request",
                }
            )

        # Set rate limit (1 minute)
        django_cache.set(user_key, True, 60)

        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "error": "Authentication required"})

        # Check if user is a patient

        user_profile = request.user.userprofile
        if user_profile.role != "patient":
            return JsonResponse(
                {"success": False, "error": "Only patients can book appointments"}
            )

        # Parse JSON data
        import json

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data"})

        # Extract booking data
        doctor_id = data.get("doctor_id")
        appointment_date = data.get("date")
        appointment_time = data.get("time")
        appointment_type = data.get("type")
        notes = data.get("notes", "")

        # Validate required fields
        if not all([doctor_id, appointment_date, appointment_time, appointment_type]):
            return JsonResponse({"success": False, "error": "Missing required fields"})

        # Use the appointment service to book
        appointment_service = AppointmentService()

        # Parse date and time
        apt_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
        apt_time = datetime.strptime(appointment_time, "%I:%M %p").time()

        # Map appointment types
        type_mapping = {
            "Consultation": "consultation",
            "Follow-up": "follow_up",
            "Checkup": "checkup",
            "Emergency": "emergency",
        }

        appointment = appointment_service.book_appointment(
            patient=request.user,
            doctor_id=int(doctor_id),
            appointment_date=apt_date,
            start_time=apt_time,
            appointment_type=type_mapping.get(appointment_type, "consultation"),
            patient_notes=notes,
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Appointment booked successfully!",
                "appointment_id": appointment.id,
                "appointment_date": appointment.appointment_date.strftime("%Y-%m-%d"),
                "appointment_time": appointment.start_time.strftime("%I:%M %p"),
            }
        )

    except Exception as e:
        logger.error(f"Book appointment error: {e}")
        return JsonResponse({"success": False, "error": str(e)})
