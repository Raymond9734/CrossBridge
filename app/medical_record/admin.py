from django.contrib import admin
from .models import MedicalRecord, Prescription, LabResult, Review


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


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = (
        "medication_name",
        "dosage",
        "frequency",
        "get_patient_name",
        "is_active",
        "date_prescribed",
    )
    list_filter = ("is_active", "date_prescribed", "is_generic_allowed")
    search_fields = (
        "medication_name",
        "medical_record__appointment__patient__first_name",
        "medical_record__appointment__patient__last_name",
    )

    def get_patient_name(self, obj):
        return obj.patient.get_full_name()

    get_patient_name.short_description = "Patient"


@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = (
        "test_name",
        "test_type",
        "status",
        "get_patient_name",
        "result_date",
    )
    list_filter = ("test_type", "status", "ordered_date", "result_date")
    search_fields = (
        "test_name",
        "medical_record__appointment__patient__first_name",
        "medical_record__appointment__patient__last_name",
    )

    def get_patient_name(self, obj):
        return obj.medical_record.patient.get_full_name()

    get_patient_name.short_description = "Patient"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "get_patient_name",
        "get_doctor_name",
        "rating",
        "is_verified",
        "is_anonymous",
        "created_at",
    )
    list_filter = ("rating", "is_verified", "is_anonymous", "created_at")
    search_fields = (
        "patient__first_name",
        "patient__last_name",
        "doctor__first_name",
        "doctor__last_name",
        "review_text",
    )

    def get_patient_name(self, obj):
        return "Anonymous" if obj.is_anonymous else obj.patient.get_full_name()

    get_patient_name.short_description = "Patient"

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.get_full_name()}"

    get_doctor_name.short_description = "Doctor"
