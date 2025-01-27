import pytest
from asgiref.sync import sync_to_async
import factory

from dataportal.models import Strain, Species
from dataportal.schemas import GenomePaginationSchema, GenomeResponseSchema
from dataportal.services.genome_service import GenomeService
from dataportal.tests.factories.species_factory import SpeciesFactory
from dataportal.tests.factories.strain_factory import StrainFactory
from dataportal.utils.exceptions import GenomeNotFoundError


@pytest.fixture
def shared_species():
    # Create reusable species objects for tests
    species_bu = SpeciesFactory(scientific_name="Bacteroides uniformis")
    species_pv = SpeciesFactory(scientific_name="Phocaeicola vulgatus")
    return species_bu, species_pv


# Cleanup database before each test
@pytest.fixture(autouse=True)
def cleanup_test_database(django_db_blocker):
    with django_db_blocker.unblock():
        Strain.objects.all().delete()
        Species.objects.all().delete()
        # Reset sequences to avoid conflicts
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='dataportal_strain'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='dataportal_species'")


# Test class for GenomeService
@pytest.mark.django_db(transaction=True)
class TestGenomeService:
    def test_strain_species_mapping(self, shared_species):
        # Pre-create species
        species_bu, species_pv = shared_species

        # Create strains with pre-defined species
        strain1 = StrainFactory(isolate_name="BU_ATCC8492", species=species_bu)
        strain2 = StrainFactory(isolate_name="PV_ATCC8482", species=species_pv)

        # Assert the species linkage
        assert strain1.species == species_bu
        assert strain2.species == species_pv

    @pytest.mark.asyncio
    async def test_get_type_strains(self, shared_species):
        # Pre-create species
        species_bu, species_pv = shared_species

        # Create strains with type_strain values
        await sync_to_async(StrainFactory.create_batch)(
            4,
            type_strain=factory.Iterator([True, False, False, True]),
            species=factory.Iterator([species_bu, species_bu, species_pv, species_pv]),
        )

        service = GenomeService()
        result = await service.get_type_strains()

        assert len(result) == 2  # Two type strains
        assert isinstance(result[0], GenomeResponseSchema)
        assert result[0].type_strain is True

    @pytest.mark.asyncio
    async def test_search_genomes_by_string(self, shared_species):
        species_bu, _ = shared_species

        # Create strains linked to species
        await sync_to_async(StrainFactory.create_batch)(
            3, isolate_name=factory.Iterator(["BU_TestStrain1", "BU_TestStrain2", "BU_TestStrain3"]), species=species_bu
        )

        service = GenomeService()
        result = await service.search_genomes_by_string(query="BU")

        print(f"Query results: {[(genome.id, genome.isolate_name) for genome in result.results]}")  # Debugging

        assert isinstance(result, GenomePaginationSchema)
        assert len(result.results) == 3
        assert all("BU" in strain.isolate_name for strain in result.results)

    @pytest.mark.asyncio
    async def test_get_genomes_by_species(self, shared_species):
        species_bu, _ = shared_species

        # Create strains for the species
        await sync_to_async(StrainFactory.create_batch)(3, species=species_bu)

        service = GenomeService()
        result = await service.get_genomes_by_species(species_id=species_bu.id)

        assert isinstance(result, GenomePaginationSchema)
        assert len(result.results) == 3
        assert all(strain.species_id == species_bu.id for strain in result.results)

    @pytest.mark.asyncio
    async def test_get_genome_by_id(self, shared_species):
        species_bu, _ = shared_species

        # Create a single strain
        strain = await sync_to_async(StrainFactory.create)(species=species_bu)

        service = GenomeService()
        result = await service.get_genome_by_id(strain.id)

        assert result.id == strain.id
        assert result.isolate_name == strain.isolate_name

    @pytest.mark.asyncio
    async def test_get_genome_by_strain_name(self, shared_species):
        species_bu, _ = shared_species

        # Create a single strain
        strain = await sync_to_async(StrainFactory.create)(
            isolate_name="Test_Strain_001", species=species_bu
        )

        print(f"Strain species: {strain.species}, Type: {type(strain.species)}")  # Debugging

        service = GenomeService()
        result = await service.get_genome_by_strain_name("Test_Strain_001")

        assert result.isolate_name == "Test_Strain_001"
        assert result.species.scientific_name == "Bacteroides uniformis"

#
# @pytest.mark.django_db
# @pytest.mark.asyncio
# async def test_get_genomes_by_species(mocker):
#     service = GenomeService()
#     result = await service.get_genomes_by_species(species_id=1)
#
#     # Validate the result
#     assert isinstance(result, GenomePaginationSchema)
#     assert len(result.results) == 3
#     assert all(strain.species_id == 1 for strain in result.results)
#
#
# @pytest.mark.django_db
# @pytest.mark.asyncio
# async def test_get_genome_by_id(mocker):
#     # Create a single mock strain
#     mock_strain = await sync_to_async(StrainFactory.create)()
#
#     # Mock the get call in Strain.objects
#     mocker.patch("dataportal.models.Strain.objects.get", return_value=mock_strain)
#
#     service = GenomeService()
#     result = await service.get_genome_by_id(mock_strain.id)
#
#     # Validate the result
#     assert result.id == mock_strain.id
#     assert result.isolate_name == mock_strain.isolate_name
#
#
# @pytest.mark.django_db
# @pytest.mark.asyncio
# async def test_search_strains():
#     service = GenomeService()
#     result = await service.search_strains(query="ATCC", species_id=1)
#
#     assert len(result) == 2
#     assert all("ATCC" in strain['isolate_name'] for strain in result)
#     assert all(strain['strain_id'] is not None for strain in result)
#
#
# @pytest.mark.django_db
# @pytest.mark.asyncio
# async def test_get_genome_by_strain_name(mocker):
#     # Create a single mock strain
#     mock_strain = await sync_to_async(StrainFactory.create)(
#         isolate_name="Test_Strain_001"
#     )
#
#     service = GenomeService()
#     result = await service.get_genome_by_strain_name("Test_Strain_001")
#
#     assert result.isolate_name == "Test_Strain_001"
#
#
# @pytest.mark.django_db
# @pytest.mark.asyncio
# async def test_get_genomes_by_ids():
#     service = GenomeService()
#     result = await service.get_genomes_by_ids([1, 2, 3])
#
#     assert len(result) == 3
#     assert all(isinstance(genome, GenomeResponseSchema) for genome in result)
#     assert {genome.id for genome in result} == set([1, 2, 3])
#
#
# @pytest.mark.django_db
# @pytest.mark.asyncio
# async def test_get_genome_by_strain_name_not_found():
#     service = GenomeService()
#
#     with pytest.raises(GenomeNotFoundError):
#         await service.get_genome_by_strain_name("Non_Existent_Strain")
#
#
# @pytest.mark.django_db
# @pytest.mark.asyncio
# async def test_search_genomes_by_species_and_string():
#     service = GenomeService()
#     result = await service.search_genomes_by_species_and_string(
#         species_id=1, query="Test"
#     )
#
#     assert isinstance(result, GenomePaginationSchema)
#     assert len(result.results) > 0
#     assert all("Test" in strain.isolate_name for strain in result.results)
#     assert all(strain.species_id == 1 for strain in result.results)
