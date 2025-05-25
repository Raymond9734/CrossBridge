from django.contrib import admin
from .models import MedicalRecord


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
    list_filter = (
        "follow_up_required",
        "is_sensitive",
        "created_at",
        "appointment__appointment_date",
    )
    search_fields = (
        "appointment__patient__first_name",
        "appointment__patient__last_name",
        "appointment__doctor__first_name",
        "appointment__doctor__last_name",
        "diagnosis",
    )
    readonly_fields = ("created_at", "updated_at", "bmi", "blood_pressure")

    fieldsets = (
        ("Appointment Information", {"fields": ("appointment",)}),
        (
            "Medical Details",
            {
                "fields": (
                    "diagnosis",
                    "treatment",
                    "prescription",
                    "allergies",
                    "medications",
                    "medical_history",
                )
            },
        ),
        (
            "Vitals",
            {
                "fields": (
                    (
                        "blood_pressure_systolic",
                        "blood_pressure_diastolic",
                        "blood_pressure",
                    ),
                    ("heart_rate", "temperature"),
                    ("weight", "height", "bmi"),
                ),
                "classes": ("collapse",),
            },
        ),
        ("Follow-up", {"fields": ("follow_up_required", "follow_up_date")}),
        ("Privacy", {"fields": ("is_sensitive",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_patient_name(self, obj):
        return obj.patient.get_full_name()

    get_patient_name.short_description = "Patient"

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.get_full_name()}"

    get_doctor_name.short_description = "Doctor"

    def get_appointment_date(self, obj):
        return obj.appointment.appointment_date

    get_appointment_date.short_description = "Appointment Date"
    get_appointment_date.admin_order_field = "appointment__appointment_date"

    def has_diagnosis(self, obj):
        return bool(obj.diagnosis)

    has_diagnosis.boolean = True
    has_diagnosis.short_description = "Has Diagnosis"
