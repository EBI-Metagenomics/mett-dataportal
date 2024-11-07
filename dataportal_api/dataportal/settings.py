import os
from pathlib import Path

from decouple import Csv, Config, RepositoryEnv

config = Config(RepositoryEnv("./mett.env"))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("DJANGO_SECRET_KEY", default="replace-with-the-secret-key")
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "dataportal": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "django.db.backends": {
            "level": "INFO",
            "handlers": ["console"],
        },
    },
}

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost", cast=Csv())
CSRF_TRUSTED_ORIGINS = [
    "https://" + os.getenv("DATA_PORTAL_URL", "127.0.0.1"),
    "http://" + os.getenv("DATA_PORTAL_URL", "127.0.0.1"),
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

ROOT_URLCONF = "dataportal_api.dataportal.urls"

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
        "NAME": os.environ.get("DB_NAME", config("DB_NAME", default="postgres")),
        "USER": os.environ.get("DB_USER", config("DB_USER", default="postgres")),
        "PASSWORD": os.environ.get(
            "DB_PASSWORD", config("DB_PASSWORD", default="pass123")
        ),
        "HOST": os.environ.get("DB_HOST", config("DB_HOST", default="localhost")),
        "PORT": os.environ.get("DB_PORT", config("DB_PORT", default="5432")),
    }
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
TIME_ZONE = config("TIME_ZONE", default="UTC")
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

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",  # React app URL
]

CORS_ALLOW_ALL_ORIGINS = True  # todo remove later
APPEND_SLASH = False  # todo verify and remove

DEFAULT_LIMIT = 10
ASSEMBLY_FTP_PATH = config(
    "ASSEMBLY_FTP_PATH",
    default="http://ftp.ebi.ac.uk/pub/databases/mett/all_hd_isolates/deduplicated_assemblies/",
)
GFF_FTP_PATH = config(
    "GFF_FTP_PATH",
    default="http://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15/{}/functional_annotation/merged_gff/",
)
