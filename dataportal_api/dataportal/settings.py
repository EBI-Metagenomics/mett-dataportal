import logging
import os
import sys
from pathlib import Path

from celery.schedules import crontab

from .elasticsearch_client import init_es_connection


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "replace-with-the-secret-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"

# Environment variables for Elasticsearch
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_USER = os.getenv("ES_USER")
ES_PASSWORD = os.getenv("ES_PASSWORD")
ES_TIMEOUT = int(os.getenv("ES_TIMEOUT", 30))
ES_MAX_RETRIES = int(os.getenv("ES_MAX_RETRIES", 3))

# Feature flags
ENABLE_PYHMMER_SEARCH = os.environ.get("ENABLE_PYHMMER_SEARCH", "false").lower() == "true"


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

CELERY_TASK_QUEUES = {
    "pyhmmer_queue": {
        "exchange": "pyhmmer",
        "routing_key": "pyhmmer.search",
    }
}

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
            "propagate": False,
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
    "http://www.gut-microbes.org",
    "http://api.gut-microbes.org",
]

# Application definition
INSTALLED_APPS = [
    "django_prometheus",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "dataportal",
    "ninja",
    "django_celery_results",
    "django_celery_beat",
]

# Conditionally include PyHMMER search app based on feature flag
if ENABLE_PYHMMER_SEARCH:
    INSTALLED_APPS.append("pyhmmer_search.search.apps.PyhmmerSearchConfig")

if DEBUG:
    INSTALLED_APPS.append("debug_toolbar")

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

MIDDLEWARE += ["dataportal.middleware.RemoveCOOPHeaderMiddleware"]

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

DATABASES = {}

IS_TESTING = "pytest" in sys.modules

if not IS_TESTING:
    # Establish Elasticsearch connection
    init_es_connection(
        host=ES_HOST,
        user=ES_USER,
        password=ES_PASSWORD,
        timeout=ES_TIMEOUT,
        max_retries=ES_MAX_RETRIES,
    )

    # PostgreSQL database for meta information
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATAPORTAL_DB", "mett-dataportal-db"),
        "USER": os.environ.get("DATAPORTAL_DB_USER", "mett-dataportal-usr"),
        "PASSWORD": os.environ.get("DATAPORTAL_DB_PASSWORD", "changeme"),
        "HOST": os.environ.get("DATAPORTAL_DB_HOST", "localhost"),
        "PORT": os.environ.get("DATAPORTAL_DB_PORT", "5432"),
    }

if "pytest" in sys.argv[0]:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

    MIGRATION_MODULES = {
        "dataportal": None,
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
STATIC_URL = "/api-static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if DEBUG:
    INTERNAL_IPS = [
        "127.0.0.1",
    ]

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost").split(",")

CORS_ALLOWED_ORIGINS = [f"http://{h}" for h in ALLOWED_HOSTS] + [
    f"https://{h}" for h in ALLOWED_HOSTS
]
if DEBUG:
    CORS_ALLOWED_ORIGINS += [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
logger.info("ALLOWED_HOSTS: %s", ALLOWED_HOSTS)
logger.info("CORS_ALLOWED_ORIGINS: %s", CORS_ALLOWED_ORIGINS)

# if not DEBUG:
#     SECURE_SSL_REDIRECT = True
#     CSRF_COOKIE_SECURE = True
#     SESSION_COOKIE_SECURE = True
# else:
#     SECURE_SSL_REDIRECT = False

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

CELERY_BEAT_SCHEDULE = {
    "cleanup-task-results-weekly": {
        "task": "pyhmmer_search.tasks.cleanup_old_tasks",
        "schedule": crontab(day_of_week="sunday", hour=3),
    },
}

PYHMMER_FAA_BASE_PATH = os.environ.get("PYHMMER_FAA_BASE_PATH", "/data/pyhmmer/output/")
HMMER_DATABASES = {
    "bu_type_strains": PYHMMER_FAA_BASE_PATH + "bu_typestrains_deduplicated.faa",
    "bu_all": PYHMMER_FAA_BASE_PATH + "bu_all_strains_deduplicated.faa",
    "pv_type_strains": PYHMMER_FAA_BASE_PATH + "pv_typestrains_deduplicated.faa",
    "pv_all": PYHMMER_FAA_BASE_PATH + "pv_all_strains_deduplicated.faa",
    "bu_pv_type_strains": PYHMMER_FAA_BASE_PATH + "bu_pv_typestrains_deduplicated.faa",
    "bu_pv_all": PYHMMER_FAA_BASE_PATH + "bu_pv_all_strains_deduplicated.faa",
}
