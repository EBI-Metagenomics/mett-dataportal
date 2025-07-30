from unittest.mock import MagicMock, patch

import pytest

from dataportal.schema.species_schemas import SpeciesSchema
from dataportal.services.species_service import SpeciesService
from dataportal.utils.exceptions import ServiceError


@pytest.mark.asyncio
@patch("dataportal.services.species_service.sync_to_async")
async def test_get_all_species_empty(mock_sync_to_async):
    # Mock the actual service method instead of sync_to_async
    service = SpeciesService()

    # Mock the _execute_search method to return empty results
    with patch.object(service, "_execute_search", return_value=[]):
        result = await service.get_all_species()
        assert result == []


@pytest.mark.asyncio
@patch("dataportal.services.species_service.sync_to_async")
async def test_get_all_species(mock_sync_to_async):
    doc1 = MagicMock()
    doc1.to_dict.return_value = {
        "scientific_name": "Bacteroides uniformis",
        "common_name": "BU",
        "taxonomy_id": 123,
        "acronym": "BU",
    }

    doc2 = MagicMock()
    doc2.to_dict.return_value = {
        "scientific_name": "Phocaeicola vulgatus",
        "common_name": "PV",
        "taxonomy_id": 456,
        "acronym": "PV",
    }

    service = SpeciesService()

    # Mock the _execute_search method to return our test data
    with patch.object(service, "_execute_search", return_value=[doc1, doc2]):
        result = await service.get_all_species()

        assert len(result) == 2
        assert isinstance(result[0], SpeciesSchema)
        assert result[0].scientific_name == "Bacteroides uniformis"
        assert result[1].scientific_name == "Phocaeicola vulgatus"


@pytest.mark.asyncio
@patch("dataportal.services.species_service.sync_to_async")
async def test_get_species_by_acronym(mock_sync_to_async):
    doc = MagicMock()
    doc.to_dict.return_value = {
        "scientific_name": "Bacteroides uniformis",
        "common_name": "BU",
        "taxonomy_id": 123,
        "acronym": "BU",
    }

    service = SpeciesService()

    # Mock the _execute_search method to return our test data
    with patch.object(service, "_execute_search", return_value=[doc]):
        result = await service.get_species_by_acronym("BU")

        assert result.scientific_name == "Bacteroides uniformis"
        assert result.acronym == "BU"


@pytest.mark.asyncio
@patch("dataportal.services.species_service.sync_to_async")
async def test_get_species_by_acronym_not_found(mock_sync_to_async):
    service = SpeciesService()

    # Mock the _execute_search method to return empty results
    with patch.object(service, "_execute_search", return_value=[]):
        with pytest.raises(Exception) as excinfo:
            await service.get_species_by_acronym("ABC")

        assert "Species with acronym ABC not found" in str(excinfo.value)


@pytest.mark.asyncio
@patch("dataportal.services.species_service.sync_to_async")
async def test_get_species_by_acronym_exception(mock_sync_to_async):
    service = SpeciesService()

    # Mock the _execute_search method to raise an exception
    with patch.object(
        service, "_execute_search", side_effect=Exception("Database connection failed")
    ):
        with pytest.raises(ServiceError):
            await service.get_species_by_acronym("BU")


@pytest.mark.asyncio
@patch("dataportal.services.species_service.sync_to_async")
async def test_get_all_species_exception(mock_sync_to_async):
    service = SpeciesService()

    # Mock the _execute_search method to raise an exception
    with patch.object(
        service, "_execute_search", side_effect=Exception("Database connection failed")
    ):
        with pytest.raises(ServiceError):
            await service.get_all_species()


# New tests for ABC methods
@pytest.mark.asyncio
@patch("dataportal.services.species_service.sync_to_async")
async def test_get_by_id_success(mock_sync_to_async):
    """Test the ABC get_by_id method."""
    doc = MagicMock()
    doc.to_dict.return_value = {
        "scientific_name": "Bacteroides uniformis",
        "common_name": "BU",
        "taxonomy_id": 123,
        "acronym": "BU",
    }

    service = SpeciesService()

    # Mock the _execute_search method to return our test data
    with patch.object(service, "_execute_search", return_value=[doc]):
        result = await service.get_by_id("BU")

        assert result is not None
        assert isinstance(result, SpeciesSchema)
        assert result.scientific_name == "Bacteroides uniformis"
        assert result.acronym == "BU"


@pytest.mark.asyncio
@patch("dataportal.services.species_service.sync_to_async")
async def test_get_by_id_not_found(mock_sync_to_async):
    """Test the ABC get_by_id method when species not found."""
    service = SpeciesService()

    # Mock the _execute_search method to return empty results
    with patch.object(service, "_execute_search", return_value=[]):
        result = await service.get_by_id("INVALID")

        assert result is None


@pytest.mark.asyncio
@patch("dataportal.services.species_service.sync_to_async")
async def test_get_by_id_exception(mock_sync_to_async):
    """Test the ABC get_by_id method when exception occurs."""
    service = SpeciesService()

    # Mock the _execute_search method to raise an exception
    with patch.object(
        service, "_execute_search", side_effect=Exception("Database connection failed")
    ):
        with pytest.raises(ServiceError):
            await service.get_by_id("BU")


@pytest.mark.asyncio
@patch("dataportal.services.species_service.sync_to_async")
async def test_get_all_abc_method(mock_sync_to_async):
    """Test the ABC get_all method."""
    doc1 = MagicMock()
    doc1.to_dict.return_value = {
        "scientific_name": "Bacteroides uniformis",
        "common_name": "BU",
        "taxonomy_id": 123,
        "acronym": "BU",
    }

    doc2 = MagicMock()
    doc2.to_dict.return_value = {
        "scientific_name": "Phocaeicola vulgatus",
        "common_name": "PV",
        "taxonomy_id": 456,
        "acronym": "PV",
    }

    service = SpeciesService()

    # Mock the _execute_search method to return our test data
    with patch.object(service, "_execute_search", return_value=[doc1, doc2]):
        result = await service.get_all()

        assert len(result) == 2
        assert isinstance(result[0], SpeciesSchema)
        assert result[0].scientific_name == "Bacteroides uniformis"
        assert result[1].scientific_name == "Phocaeicola vulgatus"


@pytest.mark.asyncio
@patch("dataportal.services.species_service.sync_to_async")
async def test_get_all_abc_method_with_filters(mock_sync_to_async):
    """Test the ABC get_all method with filters."""
    doc = MagicMock()
    doc.to_dict.return_value = {
        "scientific_name": "Bacteroides uniformis",
        "common_name": "BU",
        "taxonomy_id": 123,
        "acronym": "BU",
    }

    service = SpeciesService()

    # Mock the _execute_search method to return our test data
    with patch.object(service, "_execute_search", return_value=[doc]):
        result = await service.get_all(acronym="BU")

        assert len(result) == 1
        assert isinstance(result[0], SpeciesSchema)
        assert result[0].acronym == "BU"


@pytest.mark.asyncio
@patch("dataportal.services.species_service.sync_to_async")
async def test_get_all_abc_method_exception(mock_sync_to_async):
    """Test the ABC get_all method when exception occurs."""
    service = SpeciesService()

    # Mock the _execute_search method to raise an exception
    with patch.object(
        service, "_execute_search", side_effect=Exception("Database connection failed")
    ):
        with pytest.raises(ServiceError):
            await service.get_all()


@pytest.mark.asyncio
@patch("dataportal.services.species_service.sync_to_async")
async def test_search_abc_method(mock_sync_to_async):
    """Test the ABC search method."""
    doc = MagicMock()
    doc.to_dict.return_value = {
        "scientific_name": "Bacteroides uniformis",
        "common_name": "BU",
        "taxonomy_id": 123,
        "acronym": "BU",
    }

    service = SpeciesService()

    # Mock the _execute_search method to return our test data
    with patch.object(service, "_execute_search", return_value=[doc]):
        result = await service.search({"query": "Bacteroides"})

        assert len(result) == 1
        assert isinstance(result[0], SpeciesSchema)
        assert result[0].scientific_name == "Bacteroides uniformis"


@pytest.mark.asyncio
@patch("dataportal.services.species_service.sync_to_async")
async def test_search_abc_method_exception(mock_sync_to_async):
    """Test the ABC search method when exception occurs."""
    service = SpeciesService()

    # Mock the _execute_search method to raise an exception
    with patch.object(
        service, "_execute_search", side_effect=Exception("Database connection failed")
    ):
        with pytest.raises(ServiceError):
            await service.search({"query": "test"})


@pytest.mark.asyncio
async def test_convert_hit_to_entity():
    """Test the _convert_hit_to_entity method."""
    service = SpeciesService()

    # Create a mock hit
    mock_hit = MagicMock()
    mock_hit.to_dict.return_value = {
        "scientific_name": "Bacteroides uniformis",
        "common_name": "BU",
        "taxonomy_id": 123,
        "acronym": "BU",
    }

    result = service._convert_hit_to_entity(mock_hit)

    assert isinstance(result, SpeciesSchema)
    assert result.scientific_name == "Bacteroides uniformis"
    assert result.acronym == "BU"


@pytest.mark.asyncio
async def test_create_search():
    """Test the _create_search method from base class."""
    service = SpeciesService()

    search = service._create_search()

    # Verify it's a Search object with correct index
    assert hasattr(search, "index")
    # The actual index name should match what's defined in the service
    assert service.index_name == "species_index"


@pytest.mark.asyncio
async def test_handle_elasticsearch_error():
    """Test the _handle_elasticsearch_error method from base class."""
    service = SpeciesService()

    with pytest.raises(ServiceError):
        service._handle_elasticsearch_error(Exception("Test error"), "test operation")


@pytest.mark.asyncio
async def test_validate_required_fields():
    """Test the _validate_required_fields method from base class."""
    service = SpeciesService()

    # Test with valid data
    valid_data = {"field1": "value1", "field2": "value2"}
    required_fields = ["field1", "field2"]
    service._validate_required_fields(valid_data, required_fields)  # Should not raise

    # Test with missing field
    invalid_data = {"field1": "value1"}
    with pytest.raises(ServiceError):
        service._validate_required_fields(invalid_data, required_fields)
