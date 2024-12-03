import logging
from datetime import datetime
from django.middleware.common import MiddlewareMixin

logger = logging.getLogger(__name__)


class RemoveCOOPHeaderMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Remove the Cross-Origin-Opener-Policy header if it exists
        if "Cross-Origin-Opener-Policy" in response:
            del response["Cross-Origin-Opener-Policy"]
        return response


class LoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Log the request details
        start_time = datetime.now()
        request.start_time = start_time
        logger.info(
            f"API accessed: {request.method} {request.get_full_path()} at {start_time}"
        )

    def process_response(self, request, response):
        # Log the response details
        end_time = datetime.now()
        start_time = getattr(request, "start_time", None)
        if start_time:
            duration = end_time - start_time
        else:
            duration = "unknown"

        logger.info(
            f"API response: {response.status_code} {request.get_full_path()} took {duration}"
        )
        return response
