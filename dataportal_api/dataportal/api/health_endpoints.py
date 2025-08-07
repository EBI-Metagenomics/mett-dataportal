import logging
from django.conf import settings
from ninja import Router

from ..services.service_factory import ServiceFactory

logger = logging.getLogger(__name__)

app_health_service = ServiceFactory.get_app_health_service()

health_router = Router()


@health_router.get("/health", include_in_schema=False)
def health(request):
    return app_health_service.healthz()


@health_router.get("/features", include_in_schema=False)
def get_features(request):
    """Get available features based on environment configuration."""
    features = {
        "pyhmmer_search": getattr(settings, "ENABLE_PYHMMER_SEARCH", False),
        "feedback": getattr(settings, "ENABLE_FEEDBACK", False),
    }

    # Only include natural_query if the feature is enabled
    if getattr(settings, "ENABLE_NATURAL_QUERY", False):
        features["natural_query"] = True

    return features
