import pytest
from unittest.mock import patch, AsyncMock
from dataportal.services.species_service import SpeciesService
from dataportal.schemas import SpeciesSchema


@pytest.mark.asyncio
async def test_get_all_species(mocker):
    mock_species_data = [
        SpeciesSchema(
            id=1,
            scientific_name="Bacteroides uniformis",
            common_name="Bacteroides",
            acronym="BU",
        ),
        SpeciesSchema(
            id=2,
            scientific_name="Phocaeicola vulgatus",
            common_name="Bacteroides vulgatus",
            acronym="PV",
        ),
    ]

    # Mock Species.objects.all()
    with patch("dataportal.models.Species.objects.all", return_value=mock_species_data):
        species_service = SpeciesService()
        result = await species_service.get_all_species()

        # Verify
        assert result == mock_species_data
