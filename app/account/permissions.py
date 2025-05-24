from app.core.permissions import IsAuthenticated


class IsProfileOwner(IsAuthenticated):
    """Permission to check if user is the owner of the profile."""

    def has_object_permission(self, request, view, obj):
        if not super().has_permission(request, view):
            return False

        # Check if the user owns the profile
        if hasattr(obj, "user"):
            return obj.user == request.user
        elif hasattr(obj, "user_profile"):
            return obj.user_profile.user == request.user

        return False


class IsDoctorProfile(IsAuthenticated):
    """Permission to check if user is a doctor."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        return (
            hasattr(request.user, "userprofile")
            and request.user.userprofile.role == "doctor"
        )
