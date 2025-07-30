import logging
import time
import uuid

from django.http import HttpRequest, HttpResponse
from django.middleware.common import MiddlewareMixin
from django.utils.deprecation import MiddlewareMixin as DeprecationMiddlewareMixin

logger = logging.getLogger(__name__)


class RequestIDMiddleware(MiddlewareMixin):
    """Add unique request ID to all requests for tracking."""

    def process_request(self, request: HttpRequest) -> None:
        request.id = str(uuid.uuid4())
        request.start_time = time.time()


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """Monitor request performance and log metrics."""

    def process_request(self, request: HttpRequest) -> None:
        request.start_time = time.time()

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time
            request_id = getattr(request, "id", "unknown")

            # Log performance metrics
            logger.info(
                f"Request {request_id}: {request.method} {request.path} "
                f"-> {response.status_code} in {duration:.3f}s"
            )

            # Add performance headers
            response["X-Request-ID"] = request_id
            response["X-Response-Time"] = f"{duration:.3f}s"

            # Log slow requests
            if duration > 1.0:  # Log requests taking more than 1 second
                logger.warning(
                    f"Slow request {request_id}: {request.method} {request.path} "
                    f"took {duration:.3f}s"
                )

        return response


class RemoveCOOPHeaderMiddleware(MiddlewareMixin):
    """Remove Cross-Origin-Opener-Policy header for compatibility."""

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        if "Cross-Origin-Opener-Policy" in response:
            del response["Cross-Origin-Opener-Policy"]
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to responses."""

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        # Security headers
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Remove server information
        if "Server" in response:
            del response["Server"]

        return response


class ErrorHandlingMiddleware(MiddlewareMixin):
    """Enhanced error handling and logging."""

    def process_exception(
        self, request: HttpRequest, exception: Exception
    ) -> HttpResponse | None:
        request_id = getattr(request, "id", "unknown")
        duration = time.time() - getattr(request, "start_time", time.time())

        logger.error(
            f"Exception in request {request_id}: {request.method} {request.path} "
            f"after {duration:.3f}s: {str(exception)}",
            exc_info=True,
        )

        return None


class LoggingMiddleware(DeprecationMiddlewareMixin):
    """Enhanced request/response logging."""

    def process_request(self, request: HttpRequest) -> None:
        # Use time.time() for consistency with other middleware
        if not hasattr(request, "start_time"):
            request.start_time = time.time()
        request_id = getattr(request, "id", "unknown")

        logger.info(
            f"Request {request_id}: {request.method} {request.get_full_path()} "
            f"from {request.META.get('REMOTE_ADDR', 'unknown')}"
        )

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        start_time = getattr(request, "start_time", None)
        request_id = getattr(request, "id", "unknown")

        if start_time:
            duration = time.time() - start_time
            duration_str = f"{duration:.3f}s"
        else:
            duration_str = "unknown"

        logger.info(
            f"Response {request_id}: {response.status_code} {request.get_full_path()} "
            f"took {duration_str}"
        )
        return response
