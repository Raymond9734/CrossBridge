from django.apps import AppConfig


class MedicalRecordsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.medical_record"
    verbose_name = "Medical Records"

    def ready(self):
        import app.medical_record.signals
