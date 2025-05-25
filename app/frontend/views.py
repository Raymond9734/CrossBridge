# frontend/views.py - Minimal page views for SPA
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from inertia import render as inertia_render
import json
import logging

# Import services for data fetching
from app.account.models import UserProfile
from app.account.services import UserProfileService

logger = logging.getLogger(__name__)


def login_view(request):
    """Handle login page and authentication"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email", "").strip()
            password = data.get("password")
            remember = data.get("remember", False)

            if not email or not password:
                return inertia_render(
                    request,
                    "Login",
                    props={"errors": {"general": "Email and password are required"}},
                )

            # Find user by email
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(
                    request, username=user_obj.username, password=password
                )
            except User.DoesNotExist:
                return inertia_render(
                    request,
                    "Login",
                    props={"errors": {"general": "Invalid email or password"}},
                )

            if user is not None and user.is_active:
                login(request, user)

                # Set session expiry
                if not remember:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)  # 2 weeks

                return redirect("frontend:index")
            else:
                return inertia_render(
                    request,
                    "Login",
                    props={"errors": {"general": "Invalid email or password"}},
                )

        except json.JSONDecodeError:
            return inertia_render(
                request,
                "Login",
                props={"errors": {"general": "Invalid request format"}},
            )
        except Exception as e:
            logger.error(f"Login error: {e}")
            return inertia_render(
                request,
                "Login",
                props={"errors": {"general": "An error occurred. Please try again."}},
            )

    if request.user.is_authenticated:
        return redirect("frontend:index")

    return inertia_render(request, "Login", props={})


def register_view(request):
    """Handle registration page and user creation"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_service = UserProfileService()

            first_name = data.get("firstName", "").strip()
            last_name = data.get("lastName", "").strip()
            email = data.get("email", "").strip()
            phone = data.get("phone", "").strip()
            password = data.get("password")
            confirm_password = data.get("confirmPassword")
            role = data.get("role", "")
            terms = data.get("terms", False)

            # Server-side validation
            errors = {}

            if not first_name:
                errors["firstName"] = "First name is required"
            if not last_name:
                errors["lastName"] = "Last name is required"
            if not email:
                errors["email"] = "Email is required"
            elif User.objects.filter(email=email).exists():
                errors["email"] = "An account with this email already exists"
            if not phone:
                errors["phone"] = "Phone number is required"
            if not password:
                errors["password"] = "Password is required"
            elif len(password) < 8:
                errors["password"] = "Password must be at least 8 characters"
            if password != confirm_password:
                errors["confirmPassword"] = "Passwords do not match"
            if not terms:
                errors["terms"] = "You must accept the terms and conditions"
            if role not in ["patient", "doctor"]:
                errors["role"] = "Invalid role selection"

            if errors:
                return inertia_render(
                    request, "Register", props={"errors": errors, "old": data}
                )

            # Create user using service
            user_data = {
                "email": email,
                "password": password,
                "first_name": first_name,
                "last_name": last_name,
            }

            profile_data = {
                "phone": phone,
            }

            if role == "doctor":
                doctor_data = {
                    "specialty": "General Medicine",  # Default
                    "license_number": f"LIC-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                }
                profile = user_service.create_doctor_profile(
                    user_data, profile_data, doctor_data
                )
            else:
                profile = user_service.create_patient_profile(user_data, profile_data)

            # Auto-login
            login(request, profile.user)
            return redirect("frontend:index")

        except Exception as e:
            logger.error(f"Error during registration: {e}")
            return inertia_render(
                request,
                "Register",
                props={
                    "errors": {
                        "general": "An error occurred while creating your account. Please try again."
                    },
                    "old": data if "data" in locals() else {},
                },
            )

    if request.user.is_authenticated:
        return redirect("frontend:index")

    return inertia_render(request, "Register", props={})


def forgot_password_view(request):
    """Handle forgot password page"""
    if request.method == "POST":
        # TODO: Implement password reset logic
        return inertia_render(
            request,
            "ForgotPassword",
            props={"message": "Password reset functionality coming soon"},
        )

    return inertia_render(request, "ForgotPassword", props={})


def logout_view(request):
    """Handle user logout"""
    logout(request)
    return redirect("frontend:login")


@login_required
def index(request):
    """Main SPA entry point - minimal props for initial load"""
    try:
        user_profile = get_object_or_404(UserProfile, user=request.user)

        # Only provide essential user data - everything else via API
        user_data = {
            "id": request.user.id,
            "name": request.user.get_full_name() or request.user.username,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
            "role": user_profile.role,
        }

        # Basic props for SPA initialization
        props = {
            "user": user_data,
            "csrf_token": request.META.get("CSRF_COOKIE"),
        }

        return inertia_render(request, "Index", props=props)

    except Exception as e:
        logger.error(f"Index view error for user {request.user.id}: {e}")

        # Minimal fallback
        props = {
            "user": {
                "id": request.user.id,
                "name": request.user.get_full_name() or request.user.username,
                "role": "patient",
            },
            "error": "Unable to load user data",
        }

        return inertia_render(request, "Index", props=props)
