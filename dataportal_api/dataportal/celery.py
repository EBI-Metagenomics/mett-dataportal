import os
from celery import Celery

from dataportal import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dataportal.settings")

app = Celery("dataportal")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
