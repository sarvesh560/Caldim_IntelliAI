"""
Django settings for CALDIM IntelliSolve AI backend.

Generated for Phase 1: Project Foundation.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from backend/.env or root .env
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

# -----------------------------------------------------------------------------
# Security & Environment
# -----------------------------------------------------------------------------
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "caldim-insecure-dev-secret-key-change-in-production-phase1-foundation",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

# Allowed Hosts
_allowed_hosts_str = os.getenv(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0,[::1]"
)
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_str.split(",") if h.strip()]

# -----------------------------------------------------------------------------
# Application Definition
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # Third-party apps
    "rest_framework",
    "corsheaders",
    # Local apps
    "apps.health.apps.HealthConfig",
    "apps.visitors.apps.VisitorsConfig",
    "apps.ai_engine.apps.AiEngineConfig",
    "apps.products.apps.ProductsConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

# -----------------------------------------------------------------------------
# Database Configuration (PostgreSQL Primary)
# -----------------------------------------------------------------------------
# Reads DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT (with fallback to POSTGRES_* aliases)
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "test_caldim_intellisolve")
TEST_DB_USER = os.getenv("TEST_DB_USER") or os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "caldim_user")
TEST_DB_PASSWORD = os.getenv("TEST_DB_PASSWORD") or os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "")
TEST_DB_HOST = os.getenv("TEST_DB_HOST") or os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST", "127.0.0.1")
TEST_DB_PORT = os.getenv("TEST_DB_PORT") or os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT", "5432")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME") or os.getenv("POSTGRES_DB", "caldim_intellisolve"),
        "USER": os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "caldim_user"),
        "PASSWORD": os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT", "5432"),
        "TEST": {
            "NAME": TEST_DB_NAME,
            "USER": TEST_DB_USER,
            "PASSWORD": TEST_DB_PASSWORD,
            "HOST": TEST_DB_HOST,
            "PORT": TEST_DB_PORT,
        },
    }
}

# Visitor token validity lifetime in days (default 30 days, set to 0 for no expiration)
VISITOR_TOKEN_TTL_DAYS = int(os.getenv("VISITOR_TOKEN_TTL_DAYS", "30"))

# -----------------------------------------------------------------------------
# AI Consultation Engine (Phase 3 Stage 1)
# -----------------------------------------------------------------------------
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").strip().lower()  # "openai", "mock"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
AI_REQUEST_TIMEOUT_SECONDS = int(os.getenv("AI_REQUEST_TIMEOUT_SECONDS", "30"))
AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "1"))

# -----------------------------------------------------------------------------
# Password Validation
# -----------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# -----------------------------------------------------------------------------
# Internationalization
# -----------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# Static Files
# -----------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------------------------------------------------------------------
# Django REST Framework
# -----------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_RENDERER_CLASSES": (
        ["rest_framework.renderers.JSONRenderer"]
        + (["rest_framework.renderers.BrowsableAPIRenderer"] if DEBUG else [])
    ),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "visitor_create": os.getenv("THROTTLE_RATE_VISITOR_CREATE", "10/minute"),
        "product_search": os.getenv("THROTTLE_RATE_PRODUCT_SEARCH", "60/minute"),
        "consultation_turn": os.getenv("THROTTLE_RATE_CONSULTATION_TURN", "60/minute"),
    },
}

# Number of upstream reverse proxies for client IP extraction via X-Forwarded-For
# Defaults to 0 for local direct access; set to 1+ if behind Nginx, Caddy, or Cloudflare
NUM_PROXIES = int(os.getenv("DJANGO_NUM_PROXIES", "0"))

# -----------------------------------------------------------------------------
# Cross-Origin Resource Sharing (CORS)
# -----------------------------------------------------------------------------
from corsheaders.defaults import default_headers

_cors_origins_str = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
)
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in _cors_origins_str.split(",") if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-visitor-token",
]

