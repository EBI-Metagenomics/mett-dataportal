import logging
import os

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class DataportalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dataportal"

    def ready(self):
        # Under runserver autoreload, only load registries in the child process.
        if os.environ.get("RUN_MAIN") == "false":
            return
        try:
            from dataportal.utils.species_registry import ensure_loaded as ensure_species
            from dataportal.utils.strain_registry import ensure_loaded as ensure_strains

            ensure_species()
            ensure_strains()
        except Exception as exc:
            logger.warning("Visibility registry startup load skipped: %s", exc)
