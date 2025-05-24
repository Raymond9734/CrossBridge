from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, DoctorProfile


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
    readonly_fields = ("created_at", "updated_at", "rating", "total_reviews")

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


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
