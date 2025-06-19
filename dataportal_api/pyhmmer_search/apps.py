from django.apps import AppConfig
from django.db.models.signals import post_migrate
import django.contrib.auth.management as auth_management


class PyhmmerSearchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pyhmmer_search"

    def ready(self):
        post_migrate.disconnect(auth_management.create_permissions)
