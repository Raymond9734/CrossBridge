from django.urls import path
from . import views

app_name = "frontend"

urlpatterns = [
    # Authentication pages only
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("logout/", views.logout_view, name="logout"),
    # Main SPA entry point - handles all app routes
    path("", views.index, name="index"),
    path("dashboard/", views.index, name="dashboard"),  # Redirect to SPA
    path("appointments/", views.index, name="appointments"),  # Redirect to SPA
    path("medical-records/", views.index, name="medical_records"),  # Redirect to SPA
    path("profile/", views.index, name="profile"),  # Redirect to SPA
    path("schedule/", views.index, name="schedule"),  # Redirect to SPA
    path("patients/", views.index, name="patients"),  # Redirect to SPA
]
