from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.notification"
    verbose_name = "Notifications"

    def ready(self):
        import app.notification.signals
