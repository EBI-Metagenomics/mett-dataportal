from datetime import datetime
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def log_endpoint_access(endpoint_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            logger.info(f"Endpoint: {endpoint_name} at {datetime.now()}")
            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
