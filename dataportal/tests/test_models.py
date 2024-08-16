import pytest
from asgiref.testing import ApplicationCommunicator
from django.conf import settings
from dataportal.models import Species, Strain, Gene


@pytest.mark.django_db
class TestSpeciesManager:

    @pytest.mark.asyncio
    async def test_search_species(self):
        # Set up initial data
        species = await Species.objects.acreate(scientific_name="Test Species", common_name="Test Common")
        strain = await Strain.objects.acreate(species=species, isolate_name="Test Isolate", strain_name="Test Strain",
                                              assembly_name="Test Assembly", assembly_accession="Test Accession",
                                              fasta_file="test.fasta", gff_file="test.gff")

        # Perform the search
        results = await Species.objects.search_species("Test", "species", "asc")

        # Assertions
        assert len(results) == 1
        assert results[0]['species'] == "Test Species"
        assert results[0]['isolate_name'] == "Test Isolate"

    @pytest.mark.asyncio
    async def test_autocomplete_suggestions(self):
        # Set up initial data
        species = await Species.objects.acreate(scientific_name="Test Species", common_name="Test Common")

        # Perform the autocomplete search
        suggestions = await Species.objects.autocomplete_suggestions("Test")

        # Assertions
        assert len(suggestions) > 0
        assert "Test Species (Test Common)" in suggestions
