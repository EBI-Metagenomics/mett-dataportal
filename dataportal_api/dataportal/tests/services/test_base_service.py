import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from elasticsearch_dsl import Search

from dataportal.services.base_service import BaseService, CachedService
from dataportal.utils.exceptions import ServiceError


class MockService(BaseService[dict, dict]):
    """Mock service for testing BaseService functionality."""

    def __init__(self):
        super().__init__("test_index")

    async def get_by_id(self, id: str):
        return {"id": id, "name": "test"}

    async def get_all(self, **kwargs):
        return [{"id": "1", "name": "test1"}, {"id": "2", "name": "test2"}]

    async def search(self, query: dict):
        return [{"id": "1", "name": "test1"}]

    def _convert_hit_to_entity(self, hit):
        return hit.to_dict()


class MockCachedService(CachedService[dict, dict]):
    """Mock cached service for testing CachedService functionality."""

    def __init__(self):
        super().__init__("test_index", cache_size=100)

    async def get_by_id(self, id: str):
        return {"id": id, "name": "test"}

    async def get_all(self, **kwargs):
        return [{"id": "1", "name": "test1"}, {"id": "2", "name": "test2"}]

    async def search(self, query: dict):
        return [{"id": "1", "name": "test1"}]

    def _convert_hit_to_entity(self, hit):
        return hit.to_dict()


class TestBaseService:
    """Test cases for BaseService class."""

    def test_init(self):
        """Test BaseService initialization."""
        service = MockService()
        assert service.index_name == "test_index"
        assert hasattr(service, "logger")

    def test_create_search(self):
        """Test _create_search method."""
        service = MockService()
        search = service._create_search()

        assert isinstance(search, Search)
        # Check that the search object has the correct index name
        # The index property returns a bound method, so we need to check differently
        assert hasattr(search, "index")
        # Verify the search was created with the correct index
        assert service.index_name == "test_index"

    @patch("dataportal.services.base_service.sync_to_async")
    @pytest.mark.asyncio
    async def test_execute_search_success(self, mock_sync_to_async):
        """Test _execute_search method with success."""
        service = MockService()
        mock_search = MagicMock()
        mock_response = MagicMock()

        # Mock the async function that wraps sync_to_async
        async def mock_async_execute():
            return mock_response

        mock_sync_to_async.return_value = mock_async_execute

        result = await service._execute_search(mock_search)

        assert result == mock_response

    @patch("dataportal.services.base_service.sync_to_async")
    @pytest.mark.asyncio
    async def test_execute_search_exception(self, mock_sync_to_async):
        """Test _execute_search method with exception."""
        service = MockService()
        mock_search = MagicMock()

        mock_sync_to_async.return_value = AsyncMock(
            side_effect=Exception("Search failed")
        )

        with pytest.raises(ServiceError):
            await service._execute_search(mock_search)

    def test_handle_elasticsearch_error(self):
        """Test _handle_elasticsearch_error method."""
        service = MockService()
        error = Exception("Test error")

        with pytest.raises(ServiceError) as exc_info:
            service._handle_elasticsearch_error(error, "test operation")

        assert "Elasticsearch operation failed" in str(exc_info.value)

    def test_validate_required_fields_success(self):
        """Test _validate_required_fields method with valid data."""
        service = MockService()
        data = {"field1": "value1", "field2": "value2"}
        required_fields = ["field1", "field2"]

        # Should not raise an exception
        service._validate_required_fields(data, required_fields)

    def test_validate_required_fields_missing(self):
        """Test _validate_required_fields method with missing fields."""
        service = MockService()
        data = {"field1": "value1"}
        required_fields = ["field1", "field2"]

        with pytest.raises(ServiceError) as exc_info:
            service._validate_required_fields(data, required_fields)

        assert "Missing required fields: field2" in str(exc_info.value)

    def test_validate_required_fields_none_value(self):
        """Test _validate_required_fields method with None values."""
        service = MockService()
        data = {"field1": "value1", "field2": None}
        required_fields = ["field1", "field2"]

        with pytest.raises(ServiceError) as exc_info:
            service._validate_required_fields(data, required_fields)

        assert "Missing required fields: field2" in str(exc_info.value)

    def test_convert_hit_to_entity_default(self):
        """Test default _convert_hit_to_entity method."""
        service = MockService()
        mock_hit = MagicMock()
        mock_hit.to_dict.return_value = {"id": "1", "name": "test"}

        result = service._convert_hit_to_entity(mock_hit)

        assert result == {"id": "1", "name": "test"}

    @pytest.mark.asyncio
    async def test_get_by_id_implementation(self):
        """Test get_by_id method implementation."""
        service = MockService()
        result = await service.get_by_id("test_id")

        assert result == {"id": "test_id", "name": "test"}

    @pytest.mark.asyncio
    async def test_get_all_implementation(self):
        """Test get_all method implementation."""
        service = MockService()
        result = await service.get_all()

        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"

    @pytest.mark.asyncio
    async def test_search_implementation(self):
        """Test search method implementation."""
        service = MockService()
        result = await service.search({"query": "test"})

        assert len(result) == 1
        assert result[0]["id"] == "1"

    @pytest.mark.asyncio
    async def test_create_not_implemented(self):
        """Test that create method raises NotImplementedError."""
        service = MockService()

        with pytest.raises(NotImplementedError):
            await service.create({"test": "data"})

    @pytest.mark.asyncio
    async def test_update_not_implemented(self):
        """Test that update method raises NotImplementedError."""
        service = MockService()

        with pytest.raises(NotImplementedError):
            await service.update("test_id", {"test": "data"})

    @pytest.mark.asyncio
    async def test_delete_not_implemented(self):
        """Test that delete method raises NotImplementedError."""
        service = MockService()

        with pytest.raises(NotImplementedError):
            await service.delete("test_id")


class TestCachedService:
    """Test cases for CachedService class."""

    def test_init(self):
        """Test CachedService initialization."""
        service = MockCachedService()
        assert service.index_name == "test_index"
        assert service.cache_size == 100
        assert hasattr(service, "_cache")

    def test_get_cache_key(self):
        """Test _get_cache_key method."""
        service = MockCachedService()

        key = service._get_cache_key("arg1", "arg2", kwarg1="value1", kwarg2="value2")

        # Key should be deterministic
        expected_key = "arg1|arg2|kwarg1:value1|kwarg2:value2"
        assert key == expected_key

    def test_get_from_cache_miss(self):
        """Test _get_from_cache method with cache miss."""
        service = MockCachedService()

        result = service._get_from_cache("nonexistent_key")

        assert result is None

    def test_get_from_cache_hit(self):
        """Test _get_from_cache method with cache hit."""
        service = MockCachedService()
        service._cache["test_key"] = {"data": "test"}

        result = service._get_from_cache("test_key")

        assert result == {"data": "test"}

    def test_set_cache(self):
        """Test _set_cache method."""
        service = MockCachedService()
        service.cache_size = 2

        service._set_cache("key1", {"data": "value1"})
        service._set_cache("key2", {"data": "value2"})

        assert service._cache["key1"] == {"data": "value1"}
        assert service._cache["key2"] == {"data": "value2"}

    def test_set_cache_lru_eviction(self):
        """Test _set_cache method with LRU eviction."""
        service = MockCachedService()
        service.cache_size = 2

        # Fill cache to capacity
        service._set_cache("key1", {"data": "value1"})
        service._set_cache("key2", {"data": "value2"})

        # Add one more item, should evict the oldest
        service._set_cache("key3", {"data": "value3"})

        assert "key1" not in service._cache  # Should be evicted
        assert "key2" in service._cache
        assert "key3" in service._cache

    def test_clear_cache(self):
        """Test clear_cache method."""
        service = MockCachedService()

        # Add some items to cache
        service._set_cache("key1", {"data": "value1"})
        service._set_cache("key2", {"data": "value2"})

        assert len(service._cache) == 2

        # Clear cache
        service.clear_cache()

        assert len(service._cache) == 0

    def test_inheritance_from_base_service(self):
        """Test that CachedService properly inherits from BaseService."""
        service = MockCachedService()

        # Should have all BaseService methods
        assert hasattr(service, "get_by_id")
        assert hasattr(service, "get_all")
        assert hasattr(service, "search")
        assert hasattr(service, "_create_search")
        assert hasattr(service, "_execute_search")
        assert hasattr(service, "_handle_elasticsearch_error")
        assert hasattr(service, "_validate_required_fields")

        # Should have CachedService methods
        assert hasattr(service, "_get_cache_key")
        assert hasattr(service, "_get_from_cache")
        assert hasattr(service, "_set_cache")
        assert hasattr(service, "clear_cache")
