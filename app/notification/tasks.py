from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification


@shared_task
def process_pending_notifications():
    """Process notifications that are ready to be sent."""
    pending_notifications = Notification.objects.pending_delivery()

    for notification in pending_notifications:
        try:
            # Send via different channels
            if notification.send_email:
                send_email_notification.delay(notification.id)

            if notification.send_push:
                send_push_notification.delay(notification.id)

            # Mark as sent
            notification.mark_as_sent()

        except Exception as e:
            # Log error but continue processing other notifications
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Failed to process notification {notification.id}: {e}")

    return f"Processed {pending_notifications.count()} notifications"


@shared_task
def send_email_notification(notification_id):
    """Send email notification."""
    try:
        notification = Notification.objects.get(id=notification_id)

        send_mail(
            subject=notification.title,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.user.email],
            fail_silently=False,
        )

        return f"Email sent to {notification.user.email}"

    except Notification.DoesNotExist:
        return f"Notification {notification_id} not found"
    except Exception as e:
        return f"Failed to send email: {e}"


@shared_task
def send_push_notification(notification_id):
    """Send push notification."""
    try:
        notification = Notification.objects.get(id=notification_id)

        # Here you would integrate with push notification service
        # (Firebase, Apple Push Notifications, etc.)
        # For now, we'll just log it
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"Push notification to {notification.user.email}: {notification.title}"
        )

        return f"Push notification sent to {notification.user.email}"

    except Notification.DoesNotExist:
        return f"Notification {notification_id} not found"
    except Exception as e:
        return f"Failed to send push notification: {e}"


@shared_task
def cleanup_old_notifications():
    """Clean up old read notifications."""
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=30)

    old_notifications = Notification.objects.filter(
        is_read=True, created_at__lt=cutoff_date
    )

    count = old_notifications.count()
    old_notifications.delete()

    return f"Cleaned up {count} old notifications"
