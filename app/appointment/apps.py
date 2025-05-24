from django.apps import AppConfig


class AppointmentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.appointment"
    verbose_name = "Appointments"

    def ready(self):
        import app.appointment.signals
