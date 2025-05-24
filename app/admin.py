from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import (
    UserProfile,
    DoctorProfile,
    DoctorAvailability,
    Appointment,
    MedicalRecord,
    Prescription,
    Notification,
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fields = (
        "role",
        "phone",
        "date_of_birth",
        "gender",
        "address",
        "emergency_contact",
        "emergency_phone",
        "medical_history",
        "insurance_info",
    )


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "get_role",
        "is_staff",
        "date_joined",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "userprofile__role")
    search_fields = ("username", "email", "first_name", "last_name")

    def get_role(self, obj):
        try:
            return obj.userprofile.get_role_display()
        except UserProfile.DoesNotExist:
            return "No Profile"

    get_role.short_description = "Role"
    get_role.admin_order_field = "userprofile__role"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "phone", "age", "created_at")
    list_filter = ("role", "gender", "created_at")
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "phone",
    )
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("User Information", {"fields": ("user", "role")}),
        (
            "Contact Details",
            {"fields": ("phone", "address", "emergency_contact", "emergency_phone")},
        ),
        (
            "Personal Information",
            {"fields": ("date_of_birth", "gender", "avatar", "timezone")},
        ),
        (
            "Medical Information",
            {"fields": ("medical_history", "insurance_info"), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = (
        "get_doctor_name",
        "specialty",
        "license_number",
        "years_experience",
        "rating",
        "is_available",
    )
    list_filter = ("specialty", "is_available", "accepts_new_patients", "created_at")
    search_fields = (
        "user_profile__user__first_name",
        "user_profile__user__last_name",
        "license_number",
        "specialty",
    )
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Doctor Information", {"fields": ("user_profile",)}),
        (
            "Professional Details",
            {
                "fields": (
                    "license_number",
                    "specialty",
                    "subspecialty",
                    "years_experience",
                    "bio",
                )
            },
        ),
        (
            "Practice Information",
            {"fields": ("hospital_affiliation", "clinic_address", "consultation_fee")},
        ),
        ("Availability", {"fields": ("is_available", "accepts_new_patients")}),
        ("Ratings", {"fields": ("rating", "total_reviews"), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_doctor_name(self, obj):
        return f"Dr. {obj.user_profile.user.get_full_name()}"

    get_doctor_name.short_description = "Doctor Name"
    get_doctor_name.admin_order_field = "user_profile__user__first_name"


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


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = (
        "get_patient_name",
        "get_doctor_name",
        "get_appointment_date",
        "has_diagnosis",
        "follow_up_required",
        "created_at",
    )
    list_filter = ("follow_up_required", "created_at", "appointment__appointment_date")
    search_fields = (
        "appointment__patient__first_name",
        "appointment__patient__last_name",
        "appointment__doctor__first_name",
        "appointment__doctor__last_name",
        "diagnosis",
    )
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Appointment Information", {"fields": ("appointment",)}),
        (
            "Medical Details",
            {"fields": ("diagnosis", "treatment", "prescription", "lab_results")},
        ),
        (
            "Vitals",
            {
                "fields": (
                    ("blood_pressure_systolic", "blood_pressure_diastolic"),
                    ("heart_rate", "temperature"),
                    ("weight", "height"),
                ),
                "classes": ("collapse",),
            },
        ),
        ("Follow-up", {"fields": ("follow_up_required", "follow_up_date")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_patient_name(self, obj):
        return obj.appointment.patient.get_full_name()

    get_patient_name.short_description = "Patient"

    def get_doctor_name(self, obj):
        return f"Dr. {obj.appointment.doctor.get_full_name()}"

    get_doctor_name.short_description = "Doctor"

    def get_appointment_date(self, obj):
        return obj.appointment.appointment_date

    get_appointment_date.short_description = "Appointment Date"
    get_appointment_date.admin_order_field = "appointment__appointment_date"

    def has_diagnosis(self, obj):
        return bool(obj.diagnosis)

    has_diagnosis.boolean = True
    has_diagnosis.short_description = "Has Diagnosis"


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = (
        "medication_name",
        "dosage",
        "frequency",
        "get_patient_name",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = (
        "medication_name",
        "medical_record__appointment__patient__first_name",
    )

    def get_patient_name(self, obj):
        return obj.medical_record.appointment.patient.get_full_name()

    get_patient_name.short_description = "Patient"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "notification_type", "is_read", "created_at")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("title", "message", "user__first_name", "user__last_name")
    readonly_fields = ("created_at",)

    actions = ["mark_as_read", "mark_as_unread"]

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"Marked {queryset.count()} notifications as read.")

    mark_as_read.short_description = "Mark selected notifications as read"

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(
            request, f"Marked {queryset.count()} notifications as unread."
        )

    mark_as_unread.short_description = "Mark selected notifications as unread"


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Customize admin site
admin.site.site_header = "CareBridge Administration"
admin.site.site_title = "CareBridge Admin"
admin.site.index_title = "Welcome to CareBridge Administration"
