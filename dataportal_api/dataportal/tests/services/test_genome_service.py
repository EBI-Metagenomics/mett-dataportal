import factory
import pytest
from asgiref.sync import sync_to_async

from dataportal.models import Strain, Species
from dataportal.schemas import GenomePaginationSchema, GenomeResponseSchema
from dataportal.services.genome_service import GenomeService
from dataportal.tests.factories.species_factory import SpeciesFactory
from dataportal.tests.factories.strain_factory import StrainFactory
from dataportal.utils.constants import STRAIN_FIELD_ISOLATE_NAME
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
        assert all(strain.species.id == species_bu.id for strain in result.results)

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

    @pytest.mark.asyncio
    async def test_search_genomes_by_species_and_string(self, shared_species):
        species_bu, _ = shared_species

        # Create strains matching query and species
        await sync_to_async(StrainFactory.create_batch)(
            3, isolate_name=factory.Iterator(["BU_001", "BU_002", "Other"]),
            species=species_bu
        )

        service = GenomeService()
        result = await service.search_genomes_by_species_and_string(species_id=species_bu.id, query="BU")

        assert isinstance(result, GenomePaginationSchema)
        assert len(result.results) == 2  # Only "BU_001" and "BU_002" match
        assert all("BU" in strain.isolate_name for strain in result.results)

    @pytest.mark.asyncio
    async def test_search_strains(self, shared_species):
        species_bu, _ = shared_species

        # Create strains with various names
        await sync_to_async(StrainFactory.create_batch)(
            3, isolate_name=factory.Iterator(["BU_A", "BU_B", "NotB_U"]),
            assembly_name=factory.Iterator(["Assembly1", "Assembly2", "Assembly3"]),
            species=species_bu
        )

        service = GenomeService()
        result = await service.search_strains(query="BU")

        assert len(result) == 2  # "BU_A" and "BU_B" match
        assert all("BU" in strain[STRAIN_FIELD_ISOLATE_NAME] for strain in result)

    @pytest.mark.asyncio
    async def test_get_genomes(self, shared_species):
        species_bu, _ = shared_species

        # Create strains
        await sync_to_async(StrainFactory.create_batch)(5, species=species_bu)

        service = GenomeService()
        result = await service.get_genomes()

        assert isinstance(result, GenomePaginationSchema)
        assert len(result.results) == 5

    @pytest.mark.asyncio
    async def test_get_genomes_by_ids(self, shared_species):
        species_bu, _ = shared_species

        # Create strains and capture their IDs
        strains = await sync_to_async(StrainFactory.create_batch)(3, species=species_bu)
        strain_ids = [strain.id for strain in strains]

        service = GenomeService()
        result = await service.get_genomes_by_ids(genome_ids=strain_ids)

        assert len(result) == 3
        assert all(strain.id in strain_ids for strain in result)

    @pytest.mark.asyncio
    async def test_get_genomes_by_isolate_names(self, shared_species):
        species_bu, _ = shared_species

        # Create strains with specific isolate names
        isolate_names = ["Isolate_A", "Isolate_B"]
        await sync_to_async(StrainFactory.create_batch)(
            2, isolate_name=factory.Iterator(isolate_names), species=species_bu
        )

        service = GenomeService()
        result = await service.get_genomes_by_isolate_names(isolate_names=isolate_names)

        assert len(result) == 2
        assert all(strain.isolate_name in isolate_names for strain in result)

    @pytest.mark.asyncio
    async def test_get_genomes_by_ids_empty_list(self):
        service = GenomeService()
        result = await service.get_genomes_by_ids(genome_ids=[])
        assert result == []  # Should return an empty list without error

    @pytest.mark.asyncio
    async def test_get_genomes_by_isolate_names_empty_list(self):
        service = GenomeService()
        result = await service.get_genomes_by_isolate_names(isolate_names=[])
        assert result == []  # Should return an empty list without error

    @pytest.mark.asyncio
    async def test_invalid_genome_id_raises_error(self, shared_species):
        service = GenomeService()
        invalid_id = 999  # Assuming no strain with this ID exists
        with pytest.raises(GenomeNotFoundError):
            await service.get_genome_by_id(invalid_id)

    @pytest.mark.asyncio
    async def test_invalid_genome_strain_name_raises_error(self, shared_species):
        service = GenomeService()
        invalid_name = "NonExistentStrain"
        with pytest.raises(GenomeNotFoundError):
            await service.get_genome_by_strain_name(invalid_name)
