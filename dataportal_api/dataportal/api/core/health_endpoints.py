import logging
from django.conf import settings
from ninja import Router

from dataportal.schema.response_schemas import (
    SuccessResponseSchema,
    create_success_response,
    ErrorCode,
)
from dataportal.services.service_factory import ServiceFactory
from dataportal.utils.errors import raise_http_error
from dataportal.utils.response_wrappers import wrap_success_response

logger = logging.getLogger(__name__)

app_health_service = ServiceFactory.get_app_health_service()

health_router = Router()


@health_router.get("/health", response=SuccessResponseSchema, include_in_schema=False)
@wrap_success_response
def health(request):
    """Health check endpoint."""
    health_result = app_health_service.healthz()

    # healthz() returns either:
    # - (status_code, dict) for unhealthy
    # - dict for healthy
    if isinstance(health_result, tuple):
        status_code, health_data = health_result
        message = health_data.get("reason", "Service unhealthy")
        raise_http_error(
            status_code=status_code,
            message=message,
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
        )

    return create_success_response(
        data=health_result, message="Health check completed successfully"
    )


@health_router.get("/features", response=SuccessResponseSchema, include_in_schema=False)
@wrap_success_response
def get_features(request):
    """Get available features based on environment configuration."""
    features = {
        "pyhmmer_search": getattr(settings, "ENABLE_PYHMMER_SEARCH", False),
        "feedback": getattr(settings, "ENABLE_FEEDBACK", False),
    }

    # Only include natural_query if the feature is enabled
    if getattr(settings, "ENABLE_NATURAL_QUERY", False):
        features["natural_query"] = True

    return create_success_response(data=features, message="Feature flags retrieved successfully")
