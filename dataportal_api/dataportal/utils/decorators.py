import asyncio
import functools
import logging
import time
from collections.abc import Callable

from cachetools import TTLCache

logger = logging.getLogger(__name__)


def log_execution_time(func: Callable) -> Callable:
    """Decorator to log method execution time."""

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.4f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"{func.__name__} failed after {execution_time:.4f} seconds: {e}"
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.4f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"{func.__name__} failed after {execution_time:.4f} seconds: {e}"
            )
            raise

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def cache_result(ttl: int = 300, maxsize: int = 100):
    """Decorator to cache method results with TTL."""

    def decorator(func: Callable) -> Callable:
        cache = TTLCache(maxsize=maxsize, ttl=ttl)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = (
                f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            )

            if cache_key in cache:
                logger.debug(f"Cache hit for {func.__name__}")
                return cache[cache_key]

            result = await func(*args, **kwargs)
            cache[cache_key] = result
            logger.debug(f"Cache miss for {func.__name__}, stored result")
            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = (
                f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            )

            if cache_key in cache:
                logger.debug(f"Cache hit for {func.__name__}")
                return cache[cache_key]

            result = func(*args, **kwargs)
            cache[cache_key] = result
            logger.debug(f"Cache miss for {func.__name__}, stored result")
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry method on failure."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}"
                        )
                        await asyncio.sleep(delay * (2**attempt))  # Exponential backoff
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}"
                        )

            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}"
                        )
                        time.sleep(delay * (2**attempt))  # Exponential backoff
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}"
                        )

            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def validate_input(validator_func: Callable | None = None):
    """Decorator to validate input parameters."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if validator_func:
                validation_result = validator_func(*args, **kwargs)
                if validation_result is not None and not validation_result:
                    raise ValueError(f"Input validation failed for {func.__name__}")
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if validator_func:
                validation_result = validator_func(*args, **kwargs)
                if validation_result is not None and not validation_result:
                    raise ValueError(f"Input validation failed for {func.__name__}")
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def rate_limit(calls: int, period: float):
    """Decorator to implement rate limiting."""

    def decorator(func: Callable) -> Callable:
        last_reset = time.time()
        call_count = 0

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal last_reset, call_count

            current_time = time.time()
            if current_time - last_reset >= period:
                call_count = 0
                last_reset = current_time

            if call_count >= calls:
                raise Exception(f"Rate limit exceeded for {func.__name__}")

            call_count += 1
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            nonlocal last_reset, call_count

            current_time = time.time()
            if current_time - last_reset >= period:
                call_count = 0
                last_reset = current_time

            if call_count >= calls:
                raise Exception(f"Rate limit exceeded for {func.__name__}")

            call_count += 1
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
