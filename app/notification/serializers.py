from rest_framework import serializers
from .models import Notification, NotificationTemplate, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""
    
    is_expired = serializers.ReadOnlyField()
    is_scheduled = serializers.ReadOnlyField()
    delivery_channels = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            "id", "notification_type", "priority", "title", "message",
            "is_read", "is_sent", "read_at", "sent_at", "appointment",
            "send_email", "send_sms", "send_push", "scheduled_for",
            "expires_at", "metadata", "is_expired", "is_scheduled",
            "delivery_channels", "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "is_sent", "sent_at", "is_expired", "is_scheduled",
            "delivery_channels", "created_at", "updated_at"
        ]

    def get_delivery_channels(self, obj):
        return obj.get_delivery_channels()


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for NotificationTemplate model."""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            "id", "name", "notification_type", "title_template",
            "message_template", "default_send_email", "default_send_sms",
            "default_send_push", "available_variables", "is_active",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for NotificationPreference model."""
    
    class Meta:
        model = NotificationPreference
        fields = [
            "id", "user", "email_notifications", "sms_notifications",
            "push_notifications", "appointment_reminders", "appointment_confirmations",
            "medical_record_updates", "prescription_notifications",
            "lab_result_notifications", "review_requests", "system_messages",
            "reminder_hours", "quiet_hours_start", "quiet_hours_end",
            "max_daily_notifications", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_reminder_hours(self, value):
        """Validate reminder hours list."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Reminder hours must be a list")
        
        for hour in value:
            if not isinstance(hour, int) or hour < 0 or hour > 168:  # Max 1 week
                raise serializers.ValidationError("Each reminder hour must be between 0 and 168")
        
        return value