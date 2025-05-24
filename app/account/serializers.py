from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, DoctorProfile


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "username", "date_joined"]


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""

    user = UserSerializer(read_only=True)
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "role",
            "phone",
            "date_of_birth",
            "gender",
            "address",
            "emergency_contact",
            "emergency_phone",
            "medical_history",
            "insurance_info",
            "avatar",
            "timezone",
            "full_name",
            "age",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_phone(self, value):
        """Validate phone number."""
        if (
            value
            and len(
                value.replace(" ", "")
                .replace("-", "")
                .replace("(", "")
                .replace(")", "")
            )
            < 10
        ):
            raise serializers.ValidationError(
                "Phone number must be at least 10 digits."
            )
        return value


class DoctorProfileSerializer(serializers.ModelSerializer):
    """Serializer for DoctorProfile model."""

    user_profile = UserProfileSerializer(read_only=True)
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = [
            "id",
            "user_profile",
            "license_number",
            "specialty",
            "subspecialty",
            "years_experience",
            "bio",
            "hospital_affiliation",
            "clinic_address",
            "consultation_fee",
            "rating",
            "total_reviews",
            "is_available",
            "accepts_new_patients",
            "doctor_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "rating", "total_reviews", "created_at", "updated_at"]

    def get_doctor_name(self, obj):
        """Get formatted doctor name."""
        return f"Dr. {obj.user_profile.full_name}"

    def validate_years_experience(self, value):
        """Validate years of experience."""
        if value < 0 or value > 50:
            raise serializers.ValidationError(
                "Years of experience must be between 0 and 50."
            )
        return value


class DoctorAvailabilitySerializer(serializers.Serializer):
    """Serializer for doctor availability data."""

    doctor_id = serializers.IntegerField()
    date = serializers.DateField()
    available_slots = serializers.ListField(child=serializers.TimeField())


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, default="patient")
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "confirm_password",
            "role",
            "phone",
        ]

    def validate(self, attrs):
        """Validate registration data."""
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")

        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError("User with this email already exists.")

        return attrs

    def create(self, validated_data):
        """Create user and profile."""
        validated_data.pop("confirm_password")

        # Create user
        user = User.objects.create_user(**validated_data)

        # Create profile

        return user
