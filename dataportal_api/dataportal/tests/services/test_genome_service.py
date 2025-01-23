import pytest
from asgiref.sync import sync_to_async

from dataportal.schemas import GenomePaginationSchema, GenomeResponseSchema
from dataportal.services.genome_service import GenomeService
from dataportal.tests.factories.species_factory import SpeciesFactory
from dataportal.tests.factories.strain_factory import StrainFactory


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_get_type_strains(mocker):
    # Create mock data
    mock_strains = await sync_to_async(StrainFactory.create_batch)(2, type_strain=True)

    # Mock the filter call in Strain.objects
    mocker.patch("dataportal.models.Strain.objects.filter", return_value=mock_strains)

    service = GenomeService()
    result = await service.get_type_strains()

    # Validate the result
    assert len(result) == 2
    assert isinstance(result[0], GenomeResponseSchema)
    assert result[0].type_strain is True


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_search_genomes_by_string(mocker):
    # Create mock data
    mock_strains = await sync_to_async(StrainFactory.create_batch)(2)

    # Mock database calls
    mocker.patch("dataportal.models.Strain.objects.filter", return_value=mock_strains)
    mocker.patch(
        "dataportal.models.Strain.objects.count", return_value=len(mock_strains)
    )

    service = GenomeService()
    result = await service.search_genomes_by_string(query="Strain")

    # Validate the result
    assert isinstance(result, GenomePaginationSchema)
    assert len(result.results) == 2
    assert result.total_results == 2


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_get_genomes_by_species(mocker):
    # Create mock data
    mock_species = await sync_to_async(SpeciesFactory.create)()
    mock_strains = await sync_to_async(StrainFactory.create_batch)(
        2, species=mock_species
    )

    # Mock database calls
    mocker.patch("dataportal.models.Strain.objects.filter", return_value=mock_strains)
    mocker.patch(
        "dataportal.models.Strain.objects.count", return_value=len(mock_strains)
    )

    service = GenomeService()
    result = await service.get_genomes_by_species(species_id=mock_species.id)

    # Validate the result
    assert isinstance(result, GenomePaginationSchema)
    assert len(result.results) == 2


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_get_genome_by_id(mocker):
    # Create a single mock strain
    mock_strain = await sync_to_async(StrainFactory.create)()

    # Mock the get call in Strain.objects
    mocker.patch("dataportal.models.Strain.objects.get", return_value=mock_strain)

    service = GenomeService()
    result = await service.get_genome_by_id(mock_strain.id)

    # Validate the result
    assert result.id == mock_strain.id
    assert result.isolate_name == mock_strain.isolate_name
