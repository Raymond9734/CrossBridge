from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# Import ViewSets from each app
from .v1.views import (
    # Authentication
    AuthViewSet,
    # Accounts
    UserProfileViewSet,
    DoctorProfileViewSet,
    DoctorAvailabilityViewSet,
    # Appointments
    AppointmentViewSet,
    AppointmentBookingViewSet,
    # Medical Records
    MedicalRecordViewSet,
    PrescriptionViewSet,
    LabResultViewSet,
    ReviewViewSet,
    # Notifications
    NotificationViewSet,
    NotificationPreferenceViewSet,
)

# Create router and register viewsets
router = DefaultRouter()

# Authentication routes
router.register(r"auth", AuthViewSet, basename="auth")

# Accounts routes - ADD basename parameters
router.register(r"profiles", UserProfileViewSet, basename="userprofile")
router.register(r"doctors", DoctorProfileViewSet, basename="doctorprofile")
router.register(
    r"doctor-availability", DoctorAvailabilityViewSet, basename="doctoravailability"
)

# Appointments routes - ADD basename parameters
router.register(r"appointments", AppointmentViewSet, basename="appointment")
router.register(
    r"appointment-booking", AppointmentBookingViewSet, basename="appointment-booking"
)

# Medical Records routes - ADD basename parameters
router.register(r"medical-records", MedicalRecordViewSet, basename="medicalrecord")
router.register(r"prescriptions", PrescriptionViewSet, basename="prescription")
router.register(r"lab-results", LabResultViewSet, basename="labresult")
router.register(r"reviews", ReviewViewSet, basename="review")

# Notifications routes - ADD basename parameters
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(
    r"notification-preferences",
    NotificationPreferenceViewSet,
    basename="notificationpreference",
)

# API v1 patterns
v1_patterns = [
    path("", include(router.urls)),
    path("auth/", include("rest_framework.urls")),  # DRF browsable API auth
]

# Main API patterns
urlpatterns = [
    path("v1/", include((v1_patterns, "api"), namespace="v1")),
    # API Documentation
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
