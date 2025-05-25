from django.db import router
from django.urls import path, include

from app.api.v1.views.utils import get_available_doctors_ajax, get_available_slots_ajax


# API v1 patterns
v1_patterns = [
    path("", include(router.urls)),
    path("auth/", include("rest_framework.urls")),  # DRF browsable API auth
    # AJAX utility endpoints (for backward compatibility with frontend)
    path("available-slots/", get_available_slots_ajax, name="available_slots_ajax"),
    path(
        "available-doctors/", get_available_doctors_ajax, name="available_doctors_ajax"
    ),
]
