from datetime import datetime
from ninja.middleware import Middleware
import logging

logger = logging.getLogger(__name__)


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
