from django.urls import path
from . import views

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
    # Other pages
    path("about/", views.about, name="about"),
]
