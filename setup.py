# diagnosis.py - Run this to check your Django configuration
import os
import sys
import django
from django.conf import settings
from django.apps import apps

# Add your project root to Python path
sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CareBridge.settings")

django.setup()


def diagnose_apps():
    """Diagnose Django apps and model configuration."""
    print("=== DJANGO APPS DIAGNOSIS ===\n")

    # Check installed apps
    print("1. INSTALLED_APPS:")
    for i, app in enumerate(settings.INSTALLED_APPS, 1):
        print(f"   {i}. {app}")
    print()

    # Check loaded apps
    print("2. LOADED APPS:")
    for app_config in apps.get_app_configs():
        print(f"   - {app_config.name} ({app_config.verbose_name})")

        # Check models in each app
        models = app_config.get_models()
        if models:
            print(f"     Models: {', '.join([model.__name__ for model in models])}")
        else:
            print("     No models found")
    print()

    # Check for model conflicts
    print("3. MODEL REGISTRY:")
    all_models = apps.get_models()
    model_names = {}

    for model in all_models:
        model_name = model.__name__
        app_label = model._meta.app_label

        if model_name in model_names:
            print(
                f"   ⚠️  CONFLICT: {model_name} found in both {model_names[model_name]} and {app_label}"
            )
        else:
            model_names[model_name] = app_label
            print(f"   ✅ {app_label}.{model_name}")

    print("\n=== DIAGNOSIS COMPLETE ===")

    # Check for common issues
    issues = []

    # Check if old models.py exists
    if os.path.exists("app/models.py"):
        issues.append(
            "❌ Old app/models.py file still exists - this may cause conflicts"
        )

    # Check for empty __init__.py files
    required_init_files = [
        "app/__init__.py",
        "app/account/__init__.py",
        "app/appointment/__init__.py",
        "app/medical_record/__init__.py",
        "app/notification/__init__.py",
        "app/core/__init__.py",
    ]

    for init_file in required_init_files:
        if not os.path.exists(init_file):
            issues.append(f"❌ Missing {init_file}")

    if issues:
        print("\n🔧 ISSUES TO FIX:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ No configuration issues found!")


if __name__ == "__main__":
    try:
        diagnose_apps()
    except Exception as e:
        print(f"❌ Error running diagnosis: {e}")
        print("\nThis usually means there's a configuration issue.")
        print(
            "Check your DJANGO_SETTINGS_MODULE and ensure all apps are properly configured."
        )
