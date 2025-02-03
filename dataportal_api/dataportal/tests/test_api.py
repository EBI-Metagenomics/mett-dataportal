import pytest
from django.test import Client

from dataportal.tests.factories.gene_factory import EssentialityTagFactory
from dataportal.tests.factories.species_factory import SpeciesFactory
from dataportal.tests.factories.strain_factory import StrainFactory


@pytest.fixture
def api_client():
    return Client()


@pytest.mark.django_db(transaction=True)
def test_species_list_positive(api_client):
    # Prepare test data
    SpeciesFactory(scientific_name="Bacteroides uniformis")
    SpeciesFactory(scientific_name="Phocaeicola vulgatus")

    response = api_client.get("/api/species/")

    assert response.status_code == 200
    assert len(response.json()) >= 2


@pytest.mark.django_db(transaction=True)
def test_genome_autocomplete(api_client):
    strain = StrainFactory(isolate_name="BU_Test")

    response = api_client.get("/api/genomes/autocomplete?query=bu&limit=5")

    assert response.status_code == 200
    assert len(response.json()) > 0


@pytest.mark.django_db(transaction=True)
def test_genome_by_id(api_client):
    strain = StrainFactory.create(isolate_name="BU_2243B")

    response = api_client.get(f"/api/genomes/by-ids?ids={strain.id}")

    assert response.status_code == 200, f"Unexpected response: {response.json()}"
    assert response.json()[0]["isolate_name"] == "BU_2243B"


@pytest.mark.django_db(transaction=True)
def test_gene_by_gene_id(api_client):
    strain = StrainFactory.create(isolate_name="BU_ATCC8492")
    gene = strain.genes.create(
        id=21160,
        gene_name="geneX",
        locus_tag="BU_0001",
        start_position=100,
        end_position=200,
        product="Test Product"
    )

    response = api_client.get(f"/api/genes/{gene.id}")

    assert response.status_code == 200, f"Unexpected response: {response.json()}"
    assert response.json()["gene_name"] == "geneX"


@pytest.mark.django_db(transaction=True)
def test_essentiality_by_typestrain(api_client):
    strain = StrainFactory.create(isolate_name="BU_ATCC8492")
    gene = strain.genes.create(locus_tag="BU_ATCC8492_00001")

    essentiality_tag = EssentialityTagFactory.create(name="essential")

    gene.essentiality_data.create(essentiality=essentiality_tag)

    response = api_client.get(f"/api/genomes/{strain.id}/essentiality/contig_1")

    assert response.status_code == 200, f"Unexpected response: {response.json()}"
    json_data = response.json()
    # assert json_data["BU_ATCC8492_00001"]["locus_tag"] == "BU_ATCC8492_00001"
