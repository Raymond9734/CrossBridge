"""
Common validators for the CareBridge application.
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re


def validate_phone_number(value):
    """
    Validate phone number format.
    """
    pattern = r"^\+?[\d\s\-\(\)]{10,}$"
    if not re.match(pattern, value):
        raise ValidationError(
            _(
                "Phone number must be at least 10 digits and can contain +, -, spaces, and parentheses"
            )
        )


def validate_medical_license(value):
    """
    Validate medical license number format.
    """
    pattern = r"^[A-Z]{2,4}-\d{4,8}$"
    if not re.match(pattern, value):
        raise ValidationError(_("Medical license must be in format: ABC-123456"))


def validate_appointment_time(value):
    """
    Validate appointment time is in the future.
    """
    from django.utils import timezone

    if value <= timezone.now():
        raise ValidationError(_("Appointment time must be in the future"))
