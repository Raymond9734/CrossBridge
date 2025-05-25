# api/v1/views/__init__.py
"""
API v1 Views - Modular organization
"""

# Import all ViewSets for easy access
from .auth import AuthViewSet
from .dashboard import DashboardViewSet
from .accounts import (
    UserProfileViewSet,
    DoctorProfileViewSet,
    DoctorAvailabilityViewSet,
)
from .appointments import AppointmentViewSet, AppointmentBookingViewSet
from .medical_records import (
    MedicalRecordViewSet,
    PrescriptionViewSet,
    LabResultViewSet,
    ReviewViewSet,
)
from .notifications import NotificationViewSet, NotificationPreferenceViewSet
from .patients import PatientManagementViewSet
from .system import (
    SearchViewSet,
    ReportsViewSet,
    StatisticsViewSet,
    FileUploadViewSet,
    SystemViewSet,
)
from .utils import get_available_slots_ajax, get_available_doctors_ajax

__all__ = [
    # Authentication
    "AuthViewSet",
    # Dashboard
    "DashboardViewSet",
    # Accounts
    "UserProfileViewSet",
    "DoctorProfileViewSet",
    "DoctorAvailabilityViewSet",
    # Appointments
    "AppointmentViewSet",
    "AppointmentBookingViewSet",
    # Medical Records
    "MedicalRecordViewSet",
    "PrescriptionViewSet",
    "LabResultViewSet",
    "ReviewViewSet",
    # Notifications
    "NotificationViewSet",
    "NotificationPreferenceViewSet",
    # Patient Management
    "PatientManagementViewSet",
    # System & Utilities
    "SearchViewSet",
    "ReportsViewSet",
    "StatisticsViewSet",
    "FileUploadViewSet",
    "SystemViewSet",
    # Utility Functions
    "get_available_slots_ajax",
    "get_available_doctors_ajax",
]
