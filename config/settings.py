"""
Django settings for the Ironleaf Trading & Contracting website.

Every deployment-specific value is read from the environment (a `.env` file
in the project root is loaded automatically). See `.env.example`.
"""
import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name, default=""):
    return os.environ.get(name, default).strip()


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name, default):
    try:
        return int(env(name, str(default)))
    except ValueError:
        raise ImproperlyConfigured("%s must be a whole number." % name)


def env_list(name, default=""):
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


# --------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------
DEBUG = env_bool("DJANGO_DEBUG", False)
TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG or TESTING:
        SECRET_KEY = "insecure-development-key-do-not-use-in-production"
    else:
        raise ImproperlyConfigured("Set DJANGO_SECRET_KEY in the environment or .env file.")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "pages",
    "contact",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": env("DATABASE_PATH") or BASE_DIR / "db.sqlite3",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
TIME_ZONE = "Asia/Qatar"
USE_I18N = False
USE_TZ = True

# --------------------------------------------------------------------------
# Static files (served by WhiteNoise)
# --------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

_static_backend = (
    "django.contrib.staticfiles.storage.StaticFilesStorage"
    if (DEBUG or TESTING)
    else "whitenoise.storage.CompressedManifestStaticFilesStorage"
)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": _static_backend},
}

# --------------------------------------------------------------------------
# Email: Gmail SMTP
# Gmail needs an *App Password* (Google Account > Security > 2-Step
# Verification > App passwords), not the normal account password.
# --------------------------------------------------------------------------
EMAIL_HOST = env("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD").replace(" ", "")  # Google shows app passwords in groups
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 15)

_smtp = "django.core.mail.backends.smtp.EmailBackend"
_console = "django.core.mail.backends.console.EmailBackend"
if env("EMAIL_BACKEND"):
    EMAIL_BACKEND = env("EMAIL_BACKEND")
elif EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = _smtp
else:
    # No Gmail credentials yet: print emails to the console while developing,
    # and fail loudly (enquiry is still saved) if that happens in production.
    EMAIL_BACKEND = _console if DEBUG else _smtp

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL") or EMAIL_HOST_USER or "webmaster@localhost"
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Where enquiries are delivered (comma separated). Defaults to the Gmail account itself.
CONTACT_RECIPIENT_EMAIL = env_list("CONTACT_RECIPIENT_EMAIL") or ([EMAIL_HOST_USER] if EMAIL_HOST_USER else [])

# --------------------------------------------------------------------------
# Contact form: bot prevention
# --------------------------------------------------------------------------
CAPTCHA_LENGTH = env_int("CAPTCHA_LENGTH", 4)
CAPTCHA_TTL_SECONDS = env_int("CAPTCHA_TTL_SECONDS", 600)          # code expires after 10 minutes
CAPTCHA_IMAGE_LIMIT = env_int("CAPTCHA_IMAGE_LIMIT", 40)           # new codes per session per 10 minutes
CONTACT_MIN_FILL_SECONDS = env_int("CONTACT_MIN_FILL_SECONDS", 4)  # faster than this = bot
CONTACT_FORM_MAX_AGE_SECONDS = env_int("CONTACT_FORM_MAX_AGE_SECONDS", 7200)
CONTACT_ATTEMPTS_PER_HOUR = env_int("CONTACT_ATTEMPTS_PER_HOUR", 20)   # per browser session
CONTACT_MAX_PER_HOUR = env_int("CONTACT_MAX_PER_HOUR", 3)          # saved enquiries per IP
CONTACT_MAX_PER_DAY = env_int("CONTACT_MAX_PER_DAY", 10)
# Number of reverse proxies in front of Django that append to X-Forwarded-For (0 = none).
TRUSTED_PROXY_COUNT = env_int("TRUSTED_PROXY_COUNT", 0)

# --------------------------------------------------------------------------
# Sessions / cookies
# --------------------------------------------------------------------------
SESSION_COOKIE_AGE = 60 * 60 * 24
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# --------------------------------------------------------------------------
# Production hardening (on whenever DEBUG is off)
# --------------------------------------------------------------------------
if not DEBUG and not TESTING:
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env_int("DJANGO_HSTS_SECONDS", 31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_HSTS_INCLUDE_SUBDOMAINS", False)
    SECURE_HSTS_PRELOAD = False
    if env_bool("DJANGO_BEHIND_PROXY", False):
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
