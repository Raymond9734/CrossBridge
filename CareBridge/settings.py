# CareBridge/settings.py - Enhanced Configuration
"""
Enhanced Django settings for CareBridge project with Docker, Redis, and Celery support.
"""

import os
from decouple import config
from pathlib import Path
from datetime import timedelta
import redis


def get_cache_config():
    """Get cache configuration with Redis fallback."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")

    try:
        # Test Redis connection
        r = redis.from_url(redis_url, socket_connect_timeout=1, socket_timeout=1)
        r.ping()

        # Redis is available
        print("✓ Redis connected successfully")
        return {
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": redis_url,
                "OPTIONS": {
                    "CLIENT_CLASS": "django_redis.client.DefaultClient",
                    "CONNECTION_POOL_KWARGS": {
                        "max_connections": 50,
                        "retry_on_timeout": True,
                        "socket_connect_timeout": 5,
                        "socket_timeout": 5,
                    },
                    "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
                    "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
                },
                "KEY_PREFIX": "carebridge",
                "TIMEOUT": 300,
            }
        }
    except (redis.ConnectionError, redis.TimeoutError, Exception) as e:
        print(f"⚠ Redis unavailable ({e}), falling back to local memory cache")
        return {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "carebridge-locmem",
                "OPTIONS": {
                    "MAX_ENTRIES": 10000,
                    "CULL_FREQUENCY": 4,
                },
                "TIMEOUT": 300,
            }
        }


# Use the dynamic cache configuration
CACHES = get_cache_config()

# Add cache backend info to context
CACHE_BACKEND = CACHES["default"]["BACKEND"]
IS_REDIS_CACHE = "redis" in CACHE_BACKEND.lower()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config(
    "SECRET_KEY", default="django-insecure-change-this-key-in-production"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)

APP_NAME = "CareBridge"

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=lambda v: [s.strip() for s in v.split(",")],
)
# DJANGO_VITE = {
#     "default": {
#         "dev_mode": True,
#         "dev_server_port": 5173,
#         "manifest_path": BASE_DIR / "staticfiles" / "manifest.json",
#     }
# }
# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "corsheaders",
    "django_filters",
    "django_extensions",
    "django_vite",
    "django_redis",
    "inertia",
]

LOCAL_APPS = [
    "app.core",
    "app.account",
    "app.appointment",
    "app.medical_record",
    "app.notification",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Middleware Configuration
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "inertia.middleware.InertiaMiddleware",
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

ROOT_URLCONF = "CareBridge.urls"

# Template Configuration
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "app" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "CareBridge.context_processors.debug_mode",
            ],
        },
    },
]

WSGI_APPLICATION = "CareBridge.wsgi.application"

# Database Configuration - Docker compatible
DATABASE_URL = os.environ.get("USE_POSTGRESS_DATABASE")
if DATABASE_URL:
    # Docker/Production - use DATABASE_URL
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DB_NAME"),
            "USER": config("DB_USER"),
            "PASSWORD": config("DB_PASSWORD"),
            "HOST": config("DB_HOST"),
            "PORT": config("DB_PORT"),
        }
    }
else:
    # Development fallback - SQLite
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Redis Configuration
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")

# Cache Configuration
# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": REDIS_URL,
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#             "IGNORE_EXCEPTIONS": True,  # Fail gracefully
#         },
#         "KEY_PREFIX": "carebridge",
#         "TIMEOUT": 300,  # Default timeout of 5 minutes
#     }
# }

# Session Configuration
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True

# Use Redis for sessions in production
if not DEBUG:
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"

# Celery Configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True

# Celery Beat Configuration
CELERY_BEAT_SCHEDULE = {
    "send-appointment-reminders": {
        "task": "app.appointment.tasks.send_appointment_reminders",
        "schedule": 60.0 * 60,  # Every hour
    },
    "cleanup-expired-appointments": {
        "task": "app.appointment.tasks.cleanup_expired_appointments",
        "schedule": 60.0 * 60 * 24,  # Daily
    },
    "mark-no-show-appointments": {
        "task": "app.appointment.tasks.mark_no_show_appointments",
        "schedule": 60.0 * 30,  # Every 30 minutes
    },
    "process-pending-notifications": {
        "task": "app.notification.tasks.process_pending_notifications",
        "schedule": 60.0 * 5,  # Every 5 minutes
    },
    "cleanup-old-notifications": {
        "task": "app.notification.tasks.cleanup_old_notifications",
        "schedule": 60.0 * 60 * 24,  # Daily
    },
}

# Django REST Framework Configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "appointment_booking": "10/min",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# JWT Configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Spectacular (Swagger) Configuration
SPECTACULAR_SETTINGS = {
    "TITLE": "CareBridge Healthcare Management API",
    "DESCRIPTION": "Comprehensive healthcare management system API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "displayOperationId": True,
        "defaultModelsExpandDepth": 2,
        "displayRequestDuration": True,
        "docExpansion": "list",
        "filter": True,
    },
    "SCHEMA_PATH_PREFIX": "/api/v1/",
}

# Security Configuration
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# X_FRAME_OPTIONS = "DENY"

# Production Security Settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS = True

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files and Media Configuration
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Django-Vite Configuration
DJANGO_VITE_DEV_MODE = DEBUG
DJANGO_VITE_DEV_SERVER_PORT = 5173

STATICFILES_DIRS = [
    BASE_DIR / "app" / "static" / "dist",
    BASE_DIR / "media",
]

# Inertia Configuration
INERTIA_LAYOUT = "index.html"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication settings
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"

# Custom Settings
HEALTHCARE_SETTINGS = {
    "APPOINTMENT_SLOT_DURATION": 30,  # minutes
    "MAX_APPOINTMENTS_PER_DAY": 20,
    "APPOINTMENT_REMINDER_HOURS": [24, 2],  # hours before appointment
    "MEDICAL_RECORD_RETENTION_YEARS": 7,
    "MAX_FILE_UPLOAD_SIZE": 10 * 1024 * 1024,  # 10MB
    "ALLOWED_FILE_TYPES": ["pdf", "jpg", "jpeg", "png", "doc", "docx"],
}

# Environment-specific settings
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]

    # Fix profiling conflict and exclude API routes
    DEBUG_TOOLBAR_PANELS = [
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "debug_toolbar.panels.templates.TemplatesPanel",
        "debug_toolbar.panels.cache.CachePanel",
        "debug_toolbar.panels.signals.SignalsPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
    ]

    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG
        and not request.path.startswith("/api/"),
    }

# Email Configuration
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
    EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
    EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
    EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
    DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@carebridge.com")

# Create logs directory
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Enhanced Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
        "detailed": {
            "format": "{levelname} {asctime} {name} {module} {funcName} {lineno:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file_debug": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "debug.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 5,
            "formatter": "detailed",
        },
        "file_error": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "error.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "file_app": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "app.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file_debug"],
            "level": "INFO" if not DEBUG else "DEBUG",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file_error", "console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["file_debug"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "app": {
            "handlers": ["console", "file_app", "file_error"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console", "file_app"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file_debug"],
        "level": "WARNING",
    },
}

# Error notifications for production
if not DEBUG:
    ADMINS = [
        ("Admin", config("ADMIN_EMAIL", default="rymadara97@gmail.com")),
    ]

# Create required directories
(BASE_DIR / "media").mkdir(exist_ok=True)
(BASE_DIR / "staticfiles").mkdir(exist_ok=True)
