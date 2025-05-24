from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import json

# Import services
from app.account.services import UserProfileService, DoctorProfileService
from app.appointment.services import AppointmentService, DoctorAvailabilityService
from app.medical_record.services import (
    MedicalRecordService,
    PrescriptionService,
    LabResultService,
    ReviewService,
)
from app.notification.services import NotificationService

# Import serializers
from app.account.serializers import (
    UserProfileSerializer,
    DoctorProfileSerializer,
    UserRegistrationSerializer,
)
from app.appointment.serializers import (
    AppointmentSerializer,
    DoctorAvailabilitySerializer,
    AppointmentBookingSerializer,
)
from app.medical_record.serializers import (
    MedicalRecordSerializer,
    PrescriptionSerializer,
    LabResultSerializer,
    ReviewSerializer,
)
from app.notification.serializers import (
    NotificationSerializer,
    NotificationPreferenceSerializer,
)

# Import models
from app.account.models import UserProfile, DoctorProfile
from app.appointment.models import Appointment, DoctorAvailability
from app.medical_record.models import MedicalRecord, Prescription, LabResult, Review
from app.notification.models import Notification, NotificationPreference

# Import permissions
from app.core.permissions import (
    IsPatient,
    IsDoctor,
    IsDoctorOrPatient,
    AppointmentBookingThrottle,
)
from app.account.permissions import IsProfileOwner, IsDoctorProfile


class AuthViewSet(viewsets.ViewSet):
    """Authentication endpoints."""

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @action(detail=False, methods=["post"])
    def login(self, request):
        """Login endpoint."""
        email = request.data.get("email")
        password = request.data.get("password")
        remember = request.data.get("remember", False)

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if user and user.is_active:
            login(request, user)

            # Set session expiry
            if not remember:
                request.session.set_expiry(0)

            # Get user profile data
            try:
                profile = UserProfile.objects.get(user=user)
                profile_data = UserProfileSerializer(profile).data
            except UserProfile.DoesNotExist:
                profile_data = None

            return Response({"message": "Login successful", "user": profile_data})

        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )

    @action(detail=False, methods=["post"])
    def register(self, request):
        """Registration endpoint."""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)

            # Get created profile
            profile = UserProfile.objects.get(user=user)
            profile_data = UserProfileSerializer(profile).data

            return Response(
                {"message": "Registration successful", "user": profile_data},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def logout(self, request):
        """Logout endpoint."""
        logout(request)
        return Response({"message": "Logout successful"})

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Get current user profile."""
        if request.user.is_authenticated:
            try:
                profile = UserProfile.objects.get(user=request.user)
                return Response(UserProfileSerializer(profile).data)
            except UserProfile.DoesNotExist:
                return Response(
                    {"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND
                )

        return Response(
            {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
        )


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for user profiles."""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter profiles based on user permissions."""
        user = self.request.user

        if user.is_staff:
            return UserProfile.objects.all()
        else:
            # Users can only see their own profile
            return UserProfile.objects.filter(user=user)

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [IsProfileOwner]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"])
    def dashboard_data(self, request):
        """Get dashboard data for current user."""
        try:
            profile = UserProfile.objects.get(user=request.user)
            dashboard_data = profile.get_dashboard_data()
            return Response(dashboard_data)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND
            )


class DoctorProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for doctor profiles."""

    serializer_class = DoctorProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter doctor profiles."""
        queryset = DoctorProfile.objects.select_related("user_profile__user")

        # Filter by specialty if provided
        specialty = self.request.query_params.get("specialty")
        if specialty:
            queryset = queryset.filter(specialty__icontains=specialty)

        # Filter by availability
        available_only = self.request.query_params.get("available_only")
        if available_only == "true":
            queryset = queryset.filter(is_available=True, accepts_new_patients=True)

        return queryset

    @action(detail=True, methods=["get"])
    def available_slots(self, request, pk=None):
        """Get available time slots for a doctor."""
        doctor_profile = self.get_object()
        date_str = request.query_params.get("date")

        if not date_str:
            return Response(
                {"error": "Date parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment_service = AppointmentService()
        slots = appointment_service.get_available_slots(
            doctor_profile.user_profile.user, date
        )

        return Response(
            {
                "date": date_str,
                "available_slots": [slot.strftime("%H:%M") for slot in slots],
            }
        )

    @action(detail=True, methods=["get"])
    def statistics(self, request, pk=None):
        """Get statistics for a doctor."""
        doctor_profile = self.get_object()

        # Check permission - only the doctor or admin can view stats
        if (
            request.user != doctor_profile.user_profile.user
            and not request.user.is_staff
        ):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        doctor_service = DoctorProfileService()
        stats = doctor_service.get_patient_statistics(doctor_profile.user_profile.user)

        return Response(stats)


class DoctorAvailabilityViewSet(viewsets.ModelViewSet):
    """ViewSet for doctor availability."""

    serializer_class = DoctorAvailabilitySerializer
    permission_classes = [IsDoctorProfile]

    def get_queryset(self):
        """Get availability for current doctor."""
        try:
            doctor_profile = DoctorProfile.objects.get(
                user_profile__user=self.request.user
            )
            return DoctorAvailability.objects.filter(doctor=doctor_profile)
        except DoctorProfile.DoesNotExist:
            return DoctorAvailability.objects.none()

    def perform_create(self, serializer):
        """Set doctor when creating availability."""
        doctor_profile = DoctorProfile.objects.get(user_profile__user=self.request.user)
        serializer.save(doctor=doctor_profile)

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        """Toggle availability status."""
        availability = self.get_object()
        availability_service = DoctorAvailabilityService()

        updated_availability = availability_service.toggle_availability(availability.id)

        return Response(
            {
                "message": f'Availability {"enabled" if updated_availability.is_available else "disabled"}',
                "is_available": updated_availability.is_available,
            }
        )


class AppointmentViewSet(viewsets.ModelViewSet):
    """ViewSet for appointments."""

    serializer_class = AppointmentSerializer
    permission_classes = [IsDoctorOrPatient]

    def get_queryset(self):
        """Filter appointments based on user role."""
        user = self.request.user

        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role == "doctor":
                queryset = Appointment.objects.filter(doctor=user)
            else:
                queryset = Appointment.objects.filter(patient=user)
        except UserProfile.DoesNotExist:
            return Appointment.objects.none()

        # Apply filters
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        date_from = self.request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(appointment_date__gte=date_from)

        date_to = self.request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(appointment_date__lte=date_to)

        return queryset.select_related("patient", "doctor")

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """Confirm an appointment (doctor only)."""
        appointment = self.get_object()

        # Only doctor can confirm
        if request.user != appointment.doctor:
            return Response(
                {"error": "Only the doctor can confirm appointments"},
                status=status.HTTP_403_FORBIDDEN,
            )

        appointment_service = AppointmentService()
        appointment_service.confirm_appointment(appointment)

        return Response({"message": "Appointment confirmed successfully"})

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel an appointment."""
        appointment = self.get_object()
        reason = request.data.get("reason", "")

        # Check if user can cancel this appointment
        if request.user not in [appointment.patient, appointment.doctor]:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        appointment_service = AppointmentService()
        appointment_service.cancel_appointment(appointment, request.user, reason)

        return Response({"message": "Appointment cancelled successfully"})

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark appointment as completed (doctor only)."""
        appointment = self.get_object()

        # Only doctor can mark as completed
        if request.user != appointment.doctor:
            return Response(
                {"error": "Only the doctor can complete appointments"},
                status=status.HTTP_403_FORBIDDEN,
            )

        appointment.complete()

        return Response({"message": "Appointment completed successfully"})


class AppointmentBookingViewSet(viewsets.ViewSet):
    """ViewSet for appointment booking."""

    permission_classes = [IsPatient]
    throttle_classes = [AppointmentBookingThrottle]

    @action(detail=False, methods=["post"])
    def book(self, request):
        """Book a new appointment."""
        serializer = AppointmentBookingSerializer(data=request.data)
        if serializer.is_valid():
            appointment_service = AppointmentService()

            try:
                appointment = appointment_service.book_appointment(
                    patient=request.user,
                    doctor_id=serializer.validated_data["doctor_id"],
                    appointment_date=serializer.validated_data["appointment_date"],
                    start_time=serializer.validated_data["start_time"],
                    appointment_type=serializer.validated_data["appointment_type"],
                    patient_notes=serializer.validated_data.get("patient_notes", ""),
                )

                return Response(
                    AppointmentSerializer(appointment).data,
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def available_doctors(self, request):
        """Get available doctors."""
        specialty = request.query_params.get("specialty")

        queryset = DoctorProfile.objects.filter(
            is_available=True, accepts_new_patients=True
        )
        if specialty:
            queryset = queryset.filter(specialty__icontains=specialty)

        doctors = []
        for doctor_profile in queryset.select_related("user_profile__user"):
            doctors.append(
                {
                    "id": doctor_profile.user_profile.user.id,
                    "name": f"Dr. {doctor_profile.user_profile.user.get_full_name()}",
                    "specialty": doctor_profile.specialty,
                    "rating": float(doctor_profile.rating),
                    "consultation_fee": (
                        float(doctor_profile.consultation_fee)
                        if doctor_profile.consultation_fee
                        else None
                    ),
                }
            )

        return Response({"doctors": doctors})


class MedicalRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for medical records."""

    serializer_class = MedicalRecordSerializer
    permission_classes = [IsDoctorOrPatient]

    def get_queryset(self):
        """Filter medical records based on user role."""
        user = self.request.user

        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role == "doctor":
                return MedicalRecord.objects.filter(appointment__doctor=user)
            else:
                return MedicalRecord.objects.filter(appointment__patient=user)
        except UserProfile.DoesNotExist:
            return MedicalRecord.objects.none()

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ["create", "update", "partial_update"]:
            # Only doctors can create/update medical records
            permission_classes = [IsDoctor]
        else:
            permission_classes = [IsDoctorOrPatient]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Create medical record and mark appointment as completed."""
        medical_record_service = MedicalRecordService()
        appointment = serializer.validated_data["appointment"]

        # Verify doctor can create record for this appointment
        if self.request.user != appointment.doctor:
            raise PermissionError("Can only create records for your own appointments")

        # Extract vitals and other data
        vitals = {
            "blood_pressure_systolic": serializer.validated_data.get(
                "blood_pressure_systolic"
            ),
            "blood_pressure_diastolic": serializer.validated_data.get(
                "blood_pressure_diastolic"
            ),
            "heart_rate": serializer.validated_data.get("heart_rate"),
            "temperature": serializer.validated_data.get("temperature"),
            "weight": serializer.validated_data.get("weight"),
            "height": serializer.validated_data.get("height"),
        }

        medical_record_service.create_record(
            appointment=appointment,
            diagnosis=serializer.validated_data.get("diagnosis", ""),
            treatment=serializer.validated_data.get("treatment", ""),
            vitals=vitals,
        )


class PrescriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for prescriptions."""

    serializer_class = PrescriptionSerializer
    permission_classes = [IsDoctorOrPatient]

    def get_queryset(self):
        """Filter prescriptions based on user role."""
        user = self.request.user

        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role == "doctor":
                return Prescription.objects.filter(
                    medical_record__appointment__doctor=user
                )
            else:
                return Prescription.objects.filter(
                    medical_record__appointment__patient=user
                )
        except UserProfile.DoesNotExist:
            return Prescription.objects.none()

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
        prescription = self.get_object()

        # Only prescribing doctor can deactivate
        if request.user != prescription.medical_record.appointment.doctor:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        prescription_service = PrescriptionService()
        prescription_service.deactivate_prescription(prescription)

        return Response({"message": "Prescription deactivated successfully"})


class LabResultViewSet(viewsets.ModelViewSet):
    """ViewSet for lab results."""

    serializer_class = LabResultSerializer
    permission_classes = [IsDoctorOrPatient]

    def get_queryset(self):
        """Filter lab results based on user role."""
        user = self.request.user

        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role == "doctor":
                return LabResult.objects.filter(
                    medical_record__appointment__doctor=user
                )
            else:
                return LabResult.objects.filter(
                    medical_record__appointment__patient=user
                )
        except UserProfile.DoesNotExist:
            return LabResult.objects.none()

    def get_permissions(self):
        """Only doctors can create/update lab results."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsDoctor]
        else:
            permission_classes = [IsDoctorOrPatient]

        return [permission() for permission in permission_classes]


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for reviews."""

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter reviews based on user role."""
        user = self.request.user

        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role == "doctor":
                return Review.objects.filter(doctor=user)
            else:
                return Review.objects.filter(patient=user)
        except UserProfile.DoesNotExist:
            return Review.objects.none()

    def get_permissions(self):
        """Only patients can create reviews."""
        if self.action in ["create"]:
            permission_classes = [IsPatient]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Create review and update doctor rating."""
        review_service = ReviewService()

        review_service.create_review(
            patient=self.request.user,
            doctor=serializer.validated_data["doctor"],
            appointment=serializer.validated_data.get("appointment"),
            rating=serializer.validated_data["rating"],
            review_text=serializer.validated_data.get("review_text", ""),
            detailed_ratings={
                "communication_rating": serializer.validated_data.get(
                    "communication_rating"
                ),
                "professionalism_rating": serializer.validated_data.get(
                    "professionalism_rating"
                ),
                "wait_time_rating": serializer.validated_data.get("wait_time_rating"),
            },
        )


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for notifications."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get notifications for current user."""
        queryset = Notification.objects.filter(user=self.request.user)

        # Filter by read status
        unread_only = self.request.query_params.get("unread_only")
        if unread_only == "true":
            queryset = queryset.filter(is_read=False)

        return queryset.select_related("appointment")

    def get_permissions(self):
        """Users can only view/update their own notifications."""
        if self.action in ["create", "destroy"]:
            # Only system can create/delete notifications
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        notification_service = NotificationService()

        notification_ids = request.data.get("notification_ids", [])
        if not notification_ids:
            # Mark all unread notifications as read
            notification_ids = list(
                Notification.objects.filter(
                    user=request.user, is_read=False
                ).values_list("id", flat=True)
            )

        count = notification_service.mark_as_read(notification_ids, request.user)

        return Response(
            {"message": f"Marked {count} notifications as read", "count": count}
        )

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        """Mark specific notification as read."""
        notification = self.get_object()
        notification.mark_as_read()

        return Response({"message": "Notification marked as read"})


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """ViewSet for notification preferences."""

    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get preferences for current user."""
        return NotificationPreference.objects.filter(user=self.request.user)

    def get_object(self):
        """Get or create preferences for current user."""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preferences

    def list(self, request):
        """Get current user's notification preferences."""
        preferences = self.get_object()
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)

    def update(self, request, pk=None):
        """Update notification preferences."""
        preferences = self.get_object()
        serializer = self.get_serializer(preferences, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
