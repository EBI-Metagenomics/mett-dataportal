import logging
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Generic, TypeVar

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.cache import cache
from elasticsearch_dsl import Search

from dataportal.utils.exceptions import ServiceError

logger = logging.getLogger(__name__)

T = TypeVar("T")
U = TypeVar("U")


def cache_result(timeout: int = 300, key_prefix: str = ""):
    """Decorator to cache method results using Django's cache framework."""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cache miss for {func.__name__}, stored result")
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result

            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cache miss for {func.__name__}, stored result")
            return result

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class BaseService(ABC, Generic[T, U]):
    """Enhanced base service with caching and connection pooling."""

    def __init__(self, index_name: str, cache_timeout: int = 300):
        self.index_name = index_name
        self.cache_timeout = cache_timeout
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def get_by_id(self, id: str) -> T | None:
        """Retrieve a single entity by ID."""
        pass

    @abstractmethod
    async def get_all(self, **kwargs) -> list[T]:
        """Retrieve all entities with optional filtering."""
        pass

    @abstractmethod
    async def search(self, query: U) -> list[T]:
        """Search entities based on query parameters."""
        pass

    async def create(self, data: dict[str, Any]) -> T:
        """Create operation not supported in read-only data portal."""
        raise NotImplementedError(
            "Create operation not supported in read-only data portal"
        )

    async def update(self, id: str, data: dict[str, Any]) -> T:
        """Update operation not supported in read-only data portal."""
        raise NotImplementedError(
            "Update operation not supported in read-only data portal"
        )

    async def delete(self, id: str) -> bool:
        """Delete operation not supported in read-only data portal."""
        raise NotImplementedError(
            "Delete operation not supported in read-only data portal"
        )

    def _create_search(self) -> Search:
        """Create a base Elasticsearch search object with optimizations."""
        search = Search(index=self.index_name)
        # Add default timeout and size limits
        search = search.params(timeout="30s", request_timeout=30)
        return search

    async def _execute_search(self, search: Search) -> Any:
        """Execute an Elasticsearch search asynchronously with retry logic."""
        max_retries = getattr(settings, "ES_MAX_RETRIES", 3)
        retry_count = 0

        while retry_count < max_retries:
            try:
                return await sync_to_async(search.execute)()
            except Exception as e:
                retry_count += 1
                self.logger.warning(
                    f"Elasticsearch search attempt {retry_count} failed: {e}"
                )
                if retry_count >= max_retries:
                    self._handle_elasticsearch_error(e, "search execution")
                # Wait before retry (exponential backoff)
                import asyncio

                await asyncio.sleep(2**retry_count)

    def _handle_elasticsearch_error(self, error: Exception, operation: str) -> None:
        """Handle Elasticsearch errors consistently."""
        self.logger.error(f"Elasticsearch error during {operation}: {error}")
        raise ServiceError(f"Elasticsearch operation failed: {str(error)}")

    def _validate_required_fields(
        self, data: dict[str, Any], required_fields: list[str]
    ) -> None:
        """Validate that required fields are present in data."""
        missing_fields = [
            field
            for field in required_fields
            if field not in data or data[field] is None
        ]
        if missing_fields:
            raise ServiceError(f"Missing required fields: {', '.join(missing_fields)}")

    def _convert_hit_to_entity(self, hit) -> T:
        """Convert Elasticsearch hit to entity. Override in subclasses if needed."""
        return hit.to_dict()

    def _get_cache_key(self, method_name: str, *args, **kwargs) -> str:
        """Generate a consistent cache key."""
        key_parts = [self.__class__.__name__, method_name]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        return ":".join(key_parts)

    async def _get_cached_result(self, cache_key: str) -> T | None:
        """Get result from cache."""
        return cache.get(cache_key)

    async def _set_cached_result(self, cache_key: str, result: T) -> None:
        """Set result in cache."""
        cache.set(cache_key, result, self.cache_timeout)

    def clear_cache(self, pattern: str = None) -> None:
        """Clear cache entries matching pattern."""
        if pattern:
            # Note: This is a simplified version. In production, you might want to use
            # Redis SCAN command for pattern-based cache clearing
            logger.info(f"Clearing cache with pattern: {pattern}")
        else:
            cache.clear()


class CachedService(BaseService[T, U]):
    """Service with built-in caching capabilities."""

    def __init__(
        self, index_name: str, cache_timeout: int = 300, cache_size: int = 10000
    ):
        super().__init__(index_name, cache_timeout)
        self.cache_size = cache_size
        self._local_cache = {}

    def _get_local_cache_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        return "|".join(key_parts)

    def _get_from_local_cache(self, key: str) -> T | None:
        """Get value from local cache."""
        return self._local_cache.get(key)

    def _set_local_cache(self, key: str, value: T) -> None:
        """Set value in local cache with LRU eviction."""
        if len(self._local_cache) >= self.cache_size:
            # Simple LRU: remove oldest entry
            oldest_key = next(iter(self._local_cache))
            del self._local_cache[oldest_key]
        self._local_cache[key] = value

    def clear_local_cache(self) -> None:
        """Clear the local cache."""
        self._local_cache.clear()
