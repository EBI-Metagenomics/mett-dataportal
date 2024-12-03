import logging
from datetime import datetime

from django.middleware.common import MiddlewareMixin
from ninja.middleware import Middleware

logger = logging.getLogger(__name__)


class RemoveCOOPHeaderMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Remove the Cross-Origin-Opener-Policy header if it exists
        if "Cross-Origin-Opener-Policy" in response:
            del response["Cross-Origin-Opener-Policy"]
        return response


class LoggingMiddleware(Middleware):
    def __init__(self):
        pass

    async def __call__(self, request, call_next):
        start_time = datetime.now()
        logger.info(f"API accessed: {request.method} {request.url} at {start_time}")
        response = await call_next(request)
        end_time = datetime.now()
        logger.info(
            f"API response: {response.status_code} {request.url} took {end_time - start_time}"
        )
        return response
