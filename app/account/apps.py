from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.account"
    verbose_name = "Accounts"

    def ready(self):
        import app.account.signals
