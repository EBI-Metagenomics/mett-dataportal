import pytest
from django.test import Client
from django.urls import reverse

from dataportal.models import Species, Strain


@pytest.mark.django_db
class TestSearchAPI:

    @pytest.mark.asyncio
    async def test_search_results(self):
        # Set up initial data
        species = await Species.objects.acreate(scientific_name="Test Species", common_name="Test Common")
        strain = await Strain.objects.acreate(species=species, isolate_name="Test Isolate", strain_name="Test Strain",
                                              assembly_name="Test Assembly", assembly_accession="Test Accession",
                                              fasta_file="test.fasta", gff_file="test.gff")

        client = Client()  # Django's test client
        url = reverse('api:search_results')  # Update this reverse lookup to match your route naming convention
        response = client.get(url, {'query': 'Test'})

        assert response.status_code == 200
        response_data = response.json()  # Parse JSON response
        assert len(response_data['results']) == 1
        assert response_data['results'][0]['species'] == "Test Species"

    @pytest.mark.asyncio
    async def test_autocomplete_suggestions(self):
        # Set up initial data
        species = await Species.objects.acreate(scientific_name="Test Species", common_name="Test Common")

        client = Client()  # Django's test client
        url = reverse(
            'api:autocomplete_suggestions')  # Update this reverse lookup to match your route naming convention
        response = client.get(url, {'query': 'Test'})

        assert response.status_code == 200
        response_data = response.json()  # Parse JSON response
        assert len(response_data) > 0
        assert "Test Species (Test Common)" in response_data
