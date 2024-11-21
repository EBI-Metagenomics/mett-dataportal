import pytest
from asgiref.sync import sync_to_async
from dataportal.services.species_service import SpeciesService
from dataportal.tests.factories.species_factory import SpeciesFactory


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_get_all_species():
    await sync_to_async(SpeciesFactory.create_batch)(2)

    service = SpeciesService()
    result = await service.get_all_species()

    assert len(result) == 2
    assert result[0].scientific_name == "Bacteroides uniformis"
    assert result[1].scientific_name == "Phocaeicola vulgatus"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_get_species_by_id():
    service = SpeciesService()
    result = await service.get_species_by_id(1)

    assert result.scientific_name == "Bacteroides uniformis"
    assert result.id == 1


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_get_species_by_id_not_found():
    service = SpeciesService()

    with pytest.raises(Exception) as excinfo:
        await service.get_species_by_id(999)

    assert "Error retrieving species by ID" in str(excinfo.value)
