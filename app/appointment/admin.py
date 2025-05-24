from django.contrib import admin
from django.utils.html import format_html
from .models import Appointment, DoctorAvailability


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("doctor", "get_day_name", "start_time", "end_time", "is_available")
    list_filter = ("day_of_week", "is_available")
    search_fields = (
        "doctor__user_profile__user__first_name",
        "doctor__user_profile__user__last_name",
    )

    def get_day_name(self, obj):
        return obj.get_day_of_week_display()

    get_day_name.short_description = "Day"
    get_day_name.admin_order_field = "day_of_week"


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "appointment_id",
        "get_patient_name",
        "get_doctor_name",
        "appointment_date",
        "start_time",
        "get_status_badge",
        "appointment_type",
        "created_at",
    )
    list_filter = ("status", "appointment_type", "appointment_date", "created_at")
    search_fields = (
        "patient__first_name",
        "patient__last_name",
        "doctor__first_name",
        "doctor__last_name",
        "appointment_id",
    )
    readonly_fields = ("appointment_id", "created_at", "updated_at", "duration_minutes")
    date_hierarchy = "appointment_date"

    fieldsets = (
        (
            "Appointment Details",
            {"fields": ("appointment_id", "patient", "doctor", "created_by")},
        ),
        (
            "Schedule",
            {
                "fields": (
                    "appointment_date",
                    "start_time",
                    "end_time",
                    "duration_minutes",
                )
            },
        ),
        ("Type and Status", {"fields": ("appointment_type", "status")}),
        (
            "Notes",
            {"fields": ("patient_notes", "doctor_notes"), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_patient_name(self, obj):
        return obj.patient.get_full_name()

    get_patient_name.short_description = "Patient"
    get_patient_name.admin_order_field = "patient__first_name"

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.get_full_name()}"

    get_doctor_name.short_description = "Doctor"
    get_doctor_name.admin_order_field = "doctor__first_name"

    def get_status_badge(self, obj):
        colors = {
            "pending": "#fbbf24",
            "confirmed": "#10b981",
            "in_progress": "#3b82f6",
            "completed": "#6b7280",
            "cancelled": "#ef4444",
            "no_show": "#f87171",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    get_status_badge.short_description = "Status"
    get_status_badge.admin_order_field = "status"