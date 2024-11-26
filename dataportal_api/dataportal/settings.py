import os
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "replace-with-the-secret-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "my_custom_logger": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

CSRF_TRUSTED_ORIGINS = [
    f"https://{os.environ.get('DATA_PORTAL_URL', '127.0.0.1')}",
    f"http://{os.environ.get('DATA_PORTAL_URL', '127.0.0.1')}",
]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "corsheaders",
    "dataportal",
    "ninja",
]

if DEBUG:
    INSTALLED_APPS.append("debug_toolbar")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if DEBUG:
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")

ROOT_URLCONF = "dataportal.urls"

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
WSGI_APPLICATION = "dataportal.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "postgres"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "pass123"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

if "pytest" in sys.argv[0]:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

    MIGRATION_MODULES = {
        "dataportal": None,  # Disable migrations
    }

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

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("TIME_ZONE", "Europe/London")
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if DEBUG:
    INTERNAL_IPS = [
        "127.0.0.1",
    ]

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost").split(",")

CORS_ALLOWED_ORIGINS = [f"http://{h}" for h in ALLOWED_HOSTS] + [
    f"https://{h}" for h in ALLOWED_HOSTS
]
logger.info("ALLOWED_HOSTS: %s", ALLOWED_HOSTS)
logger.info("CORS_ALLOWED_ORIGINS: %s", CORS_ALLOWED_ORIGINS)
logger.handlers[0].flush()

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
else:
    SECURE_SSL_REDIRECT = False

CORS_ALLOW_PRIVATE_NETWORK = True

APPEND_SLASH = False

DEFAULT_LIMIT = 10
ASSEMBLY_FTP_PATH = os.environ.get(
    "ASSEMBLY_FTP_PATH",
    "https://ftp.ebi.ac.uk/pub/databases/mett/all_hd_isolates/deduplicated_assemblies/",
)
GFF_FTP_PATH = os.environ.get(
    "GFF_FTP_PATH",
    "https://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15/{}/functional_annotation/merged_gff/",
)
