# Updated app/urls.py - add these to your existing urlpatterns
from django.urls import path
from ..management.command import views

urlpatterns = [
    # Main dashboard
    path("", views.index, name="index"),
    # Authentication
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    # User Profile
    path("profile/", views.profile_view, name="profile"),
    # Appointments
    path("appointments/", views.appointments_list_view, name="appointments"),
    path("book-appointment/", views.book_appointment_view, name="book_appointment"),
    # API endpoints for AJAX requests
    path("api/doctors/", views.get_available_doctors, name="api_doctors"),
    path("api/available-slots/", views.get_available_slots, name="api_available_slots"),
    path(
        "api/medical-records/", views.medical_records_view, name="api_medical_records"
    ),
    path("api/patients/", views.patients_list_view, name="api_patients"),
    # NEW: Doctor availability management endpoints
    path(
        "api/doctor-availability/",
        views.doctor_availability_view,
        name="api_doctor_availability",
    ),
    path(
        "api/toggle-availability/",
        views.toggle_availability_view,
        name="api_toggle_availability",
    ),
    path("api/days-of-week/", views.get_days_of_week, name="api_days_of_week"),
    # Add appointment cancellation endpoint if you haven't already
    path(
        "api/appointments/cancel/",
        views.cancel_appointment_view,
        name="cancel_appointment",
    ),
]
