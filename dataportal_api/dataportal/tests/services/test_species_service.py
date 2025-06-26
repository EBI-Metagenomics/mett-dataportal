from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from dataportal.schemas import SpeciesSchema
from dataportal.services.species_service import SpeciesService


@pytest.mark.asyncio
@patch("dataportal.services.species_service.sync_to_async")
async def test_get_all_species_empty(mock_sync_to_async):
    mock_sync_to_async.return_value = AsyncMock(return_value=[])

    service = SpeciesService()
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

    mock_sync_to_async.return_value = AsyncMock(return_value=[doc1, doc2])

    service = SpeciesService()
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

    mock_sync_to_async.return_value = AsyncMock(return_value=[doc])

    service = SpeciesService()
    result = await service.get_species_by_acronym("BU")

    assert result.scientific_name == "Bacteroides uniformis"
    assert result.acronym == "BU"


@pytest.mark.asyncio
@patch("dataportal.services.species_service.sync_to_async")
async def test_get_species_by_acronym_not_found(mock_sync_to_async):
    mock_sync_to_async.return_value = AsyncMock(return_value=[])

    service = SpeciesService()
    with pytest.raises(Exception) as excinfo:
        await service.get_species_by_acronym("ABC")

    assert "Error retrieving species by acronym" in str(excinfo.value)
