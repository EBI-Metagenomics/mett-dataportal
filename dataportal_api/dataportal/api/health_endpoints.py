import logging
from django.conf import settings
from ninja import Router

from ..services.app_health_service import AppHealthService

logger = logging.getLogger(__name__)

app_health_service = AppHealthService()

health_router = Router()


@health_router.get("/health")
def health(request):
    return app_health_service.healthz()


@health_router.get("/features")
def get_features(request):
    """Get available features based on environment configuration."""
    return {
        "pyhmmer_search": getattr(settings, 'ENABLE_PYHMMER_SEARCH', False)
    }
