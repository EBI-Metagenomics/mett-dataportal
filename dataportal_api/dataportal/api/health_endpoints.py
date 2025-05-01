import logging

from ninja import Router

from ..services.app_health_service import AppHealthService

logger = logging.getLogger(__name__)

app_health_service = AppHealthService()

health_router = Router()


@health_router.get("/health")
def health(request):
    return app_health_service.healthz()
