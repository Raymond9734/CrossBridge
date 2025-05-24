from django.urls import path
from . import views

app_name = "frontend"

urlpatterns = [
    # Main dashboard
    path("", views.index, name="index"),
    # Authentication pages
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    # Dashboard pages
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("appointments/", views.appointments_view, name="appointments"),
    path("medical-records/", views.medical_records_view, name="medical_records"),
    path("profile/", views.profile_view, name="profile"),
    # Doctor-specific pages
    path("schedule/", views.schedule_view, name="schedule"),
    path("patients/", views.patients_view, name="patients"),
    # AJAX endpoints for frontend
    path(
        "api/book-appointment/",
        views.book_appointment_ajax,
        name="book_appointment_ajax",
    ),
    path(
        "api/available-doctors/",
        views.get_available_doctors_ajax,
        name="get_available_doctors_ajax",
    ),
    path(
        "api/available-slots/",
        views.get_available_slots_ajax,
        name="get_available_slots_ajax",
    ),
]
