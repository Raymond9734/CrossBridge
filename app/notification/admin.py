from django.contrib import admin
from django.utils.html import format_html
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "notification_type",
        "priority",
        "get_status_badge",
        "is_sent",
        "created_at",
    )
    list_filter = ("notification_type", "priority", "is_read", "is_sent", "created_at")
    search_fields = ("title", "message", "user__first_name", "user__last_name")
    readonly_fields = ("created_at", "read_at", "sent_at")
    date_hierarchy = "created_at"

    actions = ["mark_as_read", "mark_as_unread", "mark_as_sent"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("user", "notification_type", "priority", "title", "message")},
        ),
        ("Status", {"fields": ("is_read", "read_at", "is_sent", "sent_at")}),
        (
            "Delivery",
            {
                "fields": (
                    "send_email",
                    "send_sms",
                    "send_push",
                    "scheduled_for",
                    "expires_at",
                )
            },
        ),
        ("Related", {"fields": ("appointment",)}),
        ("Metadata", {"fields": ("metadata",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_status_badge(self, obj):
        if obj.is_read:
            color = "#10b981"  # green
            status = "Read"
        else:
            color = "#f59e0b"  # yellow
            status = "Unread"

        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            status,
        )

    get_status_badge.short_description = "Status"

    def mark_as_read(self, request, queryset):
        for notification in queryset:
            notification.mark_as_read()
        self.message_user(request, f"Marked {queryset.count()} notifications as read.")

    mark_as_read.short_description = "Mark selected notifications as read"

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False, read_at=None)
        self.message_user(
            request, f"Marked {queryset.count()} notifications as unread."
        )

    mark_as_unread.short_description = "Mark selected notifications as unread"

    def mark_as_sent(self, request, queryset):
        for notification in queryset:
            notification.mark_as_sent()
        self.message_user(request, f"Marked {queryset.count()} notifications as sent.")

    mark_as_sent.short_description = "Mark selected notifications as sent"


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "email_notifications",
        "sms_notifications",
        "push_notifications",
        "max_daily_notifications",
    )
    list_filter = ("email_notifications", "sms_notifications", "push_notifications")
    search_fields = ("user__first_name", "user__last_name", "user__email")

    fieldsets = (
        ("User", {"fields": ("user",)}),
        (
            "Global Preferences",
            {
                "fields": (
                    "email_notifications",
                    "sms_notifications",
                    "push_notifications",
                )
            },
        ),
        (
            "Notification Types",
            {
                "fields": (
                    "appointment_reminders",
                    "appointment_confirmations",
                    "medical_record_updates",
                    "prescription_notifications",
                    "lab_result_notifications",
                    "review_requests",
                    "system_messages",
                )
            },
        ),
        (
            "Timing",
            {
                "fields": (
                    "reminder_hours",
                    "quiet_hours_start",
                    "quiet_hours_end",
                    "max_daily_notifications",
                )
            },
        ),
    )
