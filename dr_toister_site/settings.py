import os
from pathlib import Path

from django.contrib.messages import constants as message_constants
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def env_list(name, default=""):
    return [
        item.strip()
        for item in os.getenv(name, default).split(",")
        if item.strip()
    ]


DEBUG = env_bool("DJANGO_DEBUG", True)

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "").strip()

if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is False."
        )

    SECRET_KEY = "django-insecure-development-key"

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost",
)

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "services",
    "schedule",
    "appointments",
    "shop",
    "academy",
    "analytics",
    "crm.apps.CrmConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    ("django.contrib.sessions.middleware." "SessionMiddleware"),
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    ("django.contrib.auth.middleware." "AuthenticationMiddleware"),
    ("django.contrib.messages.middleware." "MessageMiddleware"),
    ("django.middleware.clickjacking." "XFrameOptionsMiddleware"),
]

ROOT_URLCONF = "dr_toister_site.urls"

TEMPLATES = [
    {
        "BACKEND": ("django.template.backends.django." "DjangoTemplates"),
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                ("django.template.context_processors." "request"),
                ("django.contrib.auth." "context_processors.auth"),
                ("django.contrib.messages." "context_processors.messages"),
                "shop.context_processors.cart",
                "dr_toister_site.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "dr_toister_site.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation." "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]

LANGUAGE_CODE = "uk"

TIME_ZONE = "Europe/Kyiv"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

STATICFILES_DIRS = (
    [
        BASE_DIR / "static",
    ]
    if (BASE_DIR / "static").exists()
    else []
)

STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"

MEDIA_ROOT = BASE_DIR / "media"

EMAIL_BACKEND = "django.core.mail.backends.console." "EmailBackend"

MESSAGE_TAGS = {
    message_constants.ERROR: "danger",
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"

LOGIN_REDIRECT_URL = "accounts:dashboard"

LOGOUT_REDIRECT_URL = "accounts:login"

TELEGRAM_NOTIFICATIONS_ENABLED = env_bool(
    "TELEGRAM_NOTIFICATIONS_ENABLED",
    False,
)

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN",
    "",
).strip()

TELEGRAM_ORDERS_CHAT_ID = os.getenv(
    "TELEGRAM_ORDERS_CHAT_ID",
    "",
).strip()

TELEGRAM_COURSES_CHAT_ID = os.getenv(
    "TELEGRAM_COURSES_CHAT_ID",
    "",
).strip()

TELEGRAM_BOOKINGS_CHAT_ID = os.getenv(
    "TELEGRAM_BOOKINGS_CHAT_ID",
    "",
).strip()

TELEGRAM_DAILY_REMINDER_TIME = os.getenv(
    "TELEGRAM_DAILY_REMINDER_TIME",
    "07:30",
).strip()

TELEGRAM_REQUEST_TIMEOUT = int(
    os.getenv(
        "TELEGRAM_REQUEST_TIMEOUT",
        "5",
    )
)

SITE_PHONE = os.getenv("SITE_PHONE", "").strip()

SITE_EMAIL = os.getenv("SITE_EMAIL", "").strip()

SITE_ADDRESS = os.getenv("SITE_ADDRESS", "").strip()

SITE_INSTAGRAM_URL = os.getenv("SITE_INSTAGRAM_URL", "").strip()

SITE_TELEGRAM_URL = os.getenv("SITE_TELEGRAM_URL", "").strip()

SESSION_COOKIE_HTTPONLY = True

SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

X_FRAME_OPTIONS = "DENY"

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
    SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "0"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
        "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
        False,
    )

    if env_bool("DJANGO_BEHIND_PROXY", False):
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("DJANGO_LOG_LEVEL", "WARNING"),
    },
}
