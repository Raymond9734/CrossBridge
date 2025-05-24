from inertia import share
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..models import UserProfile, Notification


class InertiaShareMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Share data that should be available to all components
        share(
            request,
            app_name=settings.APP_NAME,
            user=lambda: self._get_user_data(request),
            auth=lambda: self._get_auth_data(request),
            notifications=lambda: self._get_notifications(request),
            flash=lambda: self._get_flash_messages(request),
        )

        return self.get_response(request)

    def _get_user_data(self, request):
        """Format user data for frontend components - Legacy support"""
        if request.user.is_authenticated:
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                return {
                    "id": request.user.id,
                    "email": request.user.email,
                    "name": request.user.get_full_name() or request.user.username,
                    "first_name": request.user.first_name,
                    "last_name": request.user.last_name,
                    "role": user_profile.role,
                    "phone": user_profile.phone,
                    "address": user_profile.address,
                    "emergency_contact": user_profile.emergency_contact,
                    "is_staff": request.user.is_staff,
                }
            except UserProfile.DoesNotExist:
                # Fallback if profile doesn't exist
                UserProfile.objects.create(user=request.user)
                return {
                    "id": request.user.id,
                    "email": request.user.email,
                    "name": request.user.get_full_name() or request.user.username,
                    "role": "patient",
                    "is_staff": request.user.is_staff,
                }
        return None

    def _get_auth_data(self, request):
        """Format authentication data for frontend components"""
        if request.user.is_authenticated:
            try:
                user_profile = UserProfile.objects.get(user=request.user)

                # Get additional data based on role
                additional_data = {}
                if user_profile.role == "doctor":
                    try:
                        doctor_profile = user_profile.doctorprofile
                        additional_data.update(
                            {
                                "specialty": doctor_profile.specialty,
                                "license_number": doctor_profile.license_number,
                                "rating": float(doctor_profile.rating),
                                "is_available": doctor_profile.is_available,
                            }
                        )
                    except:
                        pass

                user_data = {
                    "id": request.user.id,
                    "username": request.user.username,
                    "email": request.user.email,
                    "name": request.user.get_full_name() or request.user.username,
                    "first_name": request.user.first_name,
                    "last_name": request.user.last_name,
                    "role": user_profile.role,
                    "phone": user_profile.phone,
                    "date_of_birth": (
                        user_profile.date_of_birth.isoformat()
                        if user_profile.date_of_birth
                        else None
                    ),
                    "gender": user_profile.gender,
                    "address": user_profile.address,
                    "emergency_contact": user_profile.emergency_contact,
                    "emergency_phone": user_profile.emergency_phone,
                    "medical_history": user_profile.medical_history,
                    "insurance_info": user_profile.insurance_info,
                    "is_staff": request.user.is_staff,
                    "is_superuser": request.user.is_superuser,
                    "date_joined": request.user.date_joined.isoformat(),
                    **additional_data,
                }

                return {
                    "user": user_data,
                    "authenticated": True,
                    "role": user_profile.role,
                }
            except UserProfile.DoesNotExist:
                # Create profile if it doesn't exist
                user_profile = UserProfile.objects.create(user=request.user)
                return {
                    "user": {
                        "id": request.user.id,
                        "username": request.user.username,
                        "email": request.user.email,
                        "name": request.user.get_full_name() or request.user.username,
                        "role": "patient",
                        "is_staff": request.user.is_staff,
                    },
                    "authenticated": True,
                    "role": "patient",
                }

        return {
            "user": None,
            "authenticated": False,
            "role": None,
        }

    def _get_notifications(self, request):
        """Get user notifications for the notification bell"""
        if request.user.is_authenticated:
            notifications = Notification.objects.filter(
                user=request.user, is_read=False
            ).order_by("-created_at")[:10]

            notifications_data = []
            for notification in notifications:
                notifications_data.append(
                    {
                        "id": notification.id,
                        "type": notification.notification_type,
                        "title": notification.title,
                        "message": notification.message,
                        "created_at": notification.created_at.isoformat(),
                        "is_read": notification.is_read,
                    }
                )

            return {"unread_count": notifications.count(), "items": notifications_data}

        return {"unread_count": 0, "items": []}

    def _get_flash_messages(self, request):
        """Get Django messages for toast notifications"""
        from django.contrib import messages

        flash_messages = []
        storage = messages.get_messages(request)

        for message in storage:
            flash_messages.append(
                {
                    "message": str(message),
                    "level": message.level_tag,
                    "tags": message.tags,
                }
            )

        return flash_messages
