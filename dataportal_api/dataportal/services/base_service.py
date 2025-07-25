from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
import logging
from elasticsearch_dsl import Search
from asgiref.sync import sync_to_async

from dataportal.utils.exceptions import ServiceError

logger = logging.getLogger(__name__)

T = TypeVar('T')
U = TypeVar('U')


class BaseService(ABC, Generic[T, U]):
    """
    Abstract base class for all read-only services in the application.
    Provides common functionality and enforces consistent interface for data presentation.
    """
    
    def __init__(self, index_name: str):
        self.index_name = index_name
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """Retrieve a single entity by ID."""
        pass
    
    @abstractmethod
    async def get_all(self, **kwargs) -> List[T]:
        """Retrieve all entities with optional filtering."""
        pass
    
    @abstractmethod
    async def search(self, query: U) -> List[T]:
        """Search entities based on query parameters."""
        pass
    
    async def create(self, data: Dict[str, Any]) -> T:
        """Create operation not supported in read-only data portal."""
        raise NotImplementedError("Create operation not supported in read-only data portal")
    
    async def update(self, id: str, data: Dict[str, Any]) -> T:
        """Update operation not supported in read-only data portal."""
        raise NotImplementedError("Update operation not supported in read-only data portal")
    
    async def delete(self, id: str) -> bool:
        """Delete operation not supported in read-only data portal."""
        raise NotImplementedError("Delete operation not supported in read-only data portal")
    
    def _create_search(self) -> Search:
        """Create a base Elasticsearch search object."""
        return Search(index=self.index_name)
    
    async def _execute_search(self, search: Search) -> Any:
        """Execute an Elasticsearch search asynchronously."""
        try:
            return await sync_to_async(search.execute)()
        except Exception as e:
            self.logger.error(f"Error executing search: {e}")
            raise ServiceError(f"Search execution failed: {str(e)}")
    
    def _handle_elasticsearch_error(self, error: Exception, operation: str) -> None:
        """Handle Elasticsearch errors consistently."""
        self.logger.error(f"Elasticsearch error during {operation}: {error}")
        raise ServiceError(f"Elasticsearch operation failed: {str(error)}")
    
    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """Validate that required fields are present in data."""
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            raise ServiceError(f"Missing required fields: {', '.join(missing_fields)}")
    
    def _convert_hit_to_entity(self, hit) -> T:
        """Convert Elasticsearch hit to entity. Override in subclasses if needed."""
        return hit.to_dict()


class CachedService(BaseService[T, U]):
    """
    Abstract base class for services that support caching.
    """
    
    def __init__(self, index_name: str, cache_size: int = 10000):
        super().__init__(index_name)
        self.cache_size = cache_size
        self._cache = {}
    
    def _get_cache_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        return "|".join(key_parts)
    
    def _get_from_cache(self, key: str) -> Optional[T]:
        """Get value from cache."""
        return self._cache.get(key)
    
    def _set_cache(self, key: str, value: T) -> None:
        """Set value in cache."""
        if len(self._cache) >= self.cache_size:
            # Simple LRU: remove oldest entry
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        self._cache[key] = value
    
    def clear_cache(self) -> None:
        """Clear the cache."""
        self._cache.clear() 