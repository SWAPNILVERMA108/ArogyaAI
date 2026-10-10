import logging

from django.apps import AppConfig
from django.contrib.auth.signals import user_login_failed

security_logger = logging.getLogger("apps.security")


def log_failed_login(sender, credentials, request=None, **kwargs):
    # Deliberately logs neither the email nor the password that was tried.
    ip = request.META.get("REMOTE_ADDR") if request is not None else None
    security_logger.warning("Login failed.", extra={"client_ip": ip})


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"

    def ready(self):
        user_login_failed.connect(log_failed_login, dispatch_uid="arogyaai_log_failed_login")
