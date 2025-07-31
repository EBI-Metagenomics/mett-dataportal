import pytest
from django.test import Client


@pytest.fixture
def api_client():
    return Client()


# @patch("dataportal.services.service_factory.ServiceFactory.get_species_service")
# @patch("django.conf.settings")
# def test_species_list_positive(mock_settings, mock_get_species_service, api_client):
#     # Mock Django settings
#     mock_settings.SESSION_ENGINE = "django.contrib.sessions.backends.db"
#     mock_settings.MIDDLEWARE = []
#     mock_settings.ROOT_URLCONF = "dataportal.urls"

#     # Mock the service factory and service
#     mock_service = MagicMock()
#     mock_get_species_service.return_value = mock_service

#     mock_doc1 = MagicMock()
#     mock_doc1.to_dict.return_value = {
#         "scientific_name": "Bacteroides uniformis",
#         "common_name": "B. uniformis",
#         "acronym": "BU",
#         "taxonomy_id": 1234,
#     }
#     mock_doc2 = MagicMock()
#     mock_doc2.to_dict.return_value = {
#         "scientific_name": "Phocaeicola vulgatus",
#         "common_name": "P. vulgatus",
#         "acronym": "PV",
#         "taxonomy_id": 5678,
#     }

#     async def mock_get_all_species():
#         return [mock_doc1, mock_doc2]

#     mock_service.get_all_species = mock_get_all_species

#     # Follow redirects to get the actual response
#     response = api_client.get("/api/species/", follow=True)
#     assert response.status_code == 200
#     assert len(response.json()) == 2
#     assert response.json()[0]["scientific_name"] == "Bacteroides uniformis"


# @patch("dataportal.services.service_factory.ServiceFactory.get_species_service")
# @patch("django.conf.settings")
# def test_species_list_empty(mock_settings, mock_get_species_service, api_client):
#     # Mock Django settings
#     mock_settings.SESSION_ENGINE = "django.contrib.sessions.backends.db"
#     mock_settings.MIDDLEWARE = []
#     mock_settings.ROOT_URLCONF = "dataportal.urls"

#     # Mock the service factory and service
#     mock_service = MagicMock()
#     mock_get_species_service.return_value = mock_service

#     async def mock_get_all_species():
#         return []

#     mock_service.get_all_species = mock_get_all_species

#     # Follow redirects to get the actual response
#     response = api_client.get("/api/species/", follow=True)
#     assert response.status_code == 200
#     assert response.json() == []


# @patch("dataportal.services.service_factory.ServiceFactory.get_genome_service")
# @patch("django.conf.settings")
# def test_genome_list_positive(mock_settings, mock_get_genome_service, api_client):
#     # Mock Django settings
#     mock_settings.SESSION_ENGINE = "django.contrib.sessions.backends.db"
#     mock_settings.MIDDLEWARE = []
#     mock_settings.ROOT_URLCONF = "dataportal.urls"

#     # Mock the service factory and service
#     mock_service = MagicMock()
#     mock_get_genome_service.return_value = mock_service

#     mock_genome1 = MagicMock()
#     mock_genome1.model_dump.return_value = {
#         "isolate_name": "BU_ATCC8492",
#         "assembly_name": "ASM001",
#         "type_strain": True,
#         "species_scientific_name": "Bacteroides uniformis",
#         "species_acronym": "BU",
#     }
#     mock_genome2 = MagicMock()
#     mock_genome2.model_dump.return_value = {
#         "isolate_name": "PV_ATCC8482",
#         "assembly_name": "ASM002",
#         "type_strain": True,
#         "species_scientific_name": "Phocaeicola vulgatus",
#         "species_acronym": "PV",
#     }

#     mock_pagination = MagicMock()
#     mock_pagination.model_dump.return_value = {
#         "results": [mock_genome1.model_dump(), mock_genome2.model_dump()],
#         "page_number": 1,
#         "num_pages": 1,
#         "has_previous": False,
#         "has_next": False,
#         "total_results": 2,
#     }

#     async def mock_get_genomes():
#         return mock_pagination

#     mock_service.get_genomes = mock_get_genomes

#     # Follow redirects to get the actual response
#     response = api_client.get("/api/genomes/", follow=True)
#     assert response.status_code == 200
#     data = response.json()
#     assert len(data["results"]) == 2
#     assert data["results"][0]["isolate_name"] == "BU_ATCC8492"


# @patch("dataportal.services.service_factory.ServiceFactory.get_gene_service")
# @patch("django.conf.settings")
# def test_gene_list_positive(mock_settings, mock_get_gene_service, api_client):
#     # Mock Django settings
#     mock_settings.SESSION_ENGINE = "django.contrib.sessions.backends.db"
#     mock_settings.MIDDLEWARE = []
#     mock_settings.ROOT_URLCONF = "dataportal.urls"

#     # Mock the service factory and service
#     mock_service = MagicMock()
#     mock_get_gene_service.return_value = mock_service

#     mock_gene1 = MagicMock()
#     mock_gene1.model_dump.return_value = {
#         "locus_tag": "BU_ATCC8492_00001",
#         "gene_name": "dnaA",
#         "isolate_name": "BU_ATCC8492",
#         "species_acronym": "BU",
#     }
#     mock_gene2 = MagicMock()
#     mock_gene2.model_dump.return_value = {
#         "locus_tag": "PV_ATCC8482_00001",
#         "gene_name": "dnaA",
#         "isolate_name": "PV_ATCC8482",
#         "species_acronym": "PV",
#     }

#     mock_pagination = MagicMock()
#     mock_pagination.model_dump.return_value = {
#         "results": [mock_gene1.model_dump(), mock_gene2.model_dump()],
#         "page_number": 1,
#         "num_pages": 1,
#         "has_previous": False,
#         "has_next": False,
#         "total_results": 2,
#     }

#     async def mock_get_all_genes():
#         return mock_pagination

#     mock_service.get_all_genes = mock_get_all_genes

#     # Follow redirects to get the actual response
#     response = api_client.get("/api/genes/", follow=True)
#     assert response.status_code == 200
#     data = response.json()
#     assert len(data["results"]) == 2
#     assert data["results"][0]["locus_tag"] == "BU_ATCC8492_00001"


# @patch("dataportal.services.service_factory.ServiceFactory.get_species_service")
# @patch("django.conf.settings")
# def test_species_by_acronym_positive(mock_settings, mock_get_species_service, api_client):
#     # Mock Django settings
#     mock_settings.SESSION_ENGINE = "django.contrib.sessions.backends.db"
#     mock_settings.MIDDLEWARE = []
#     mock_settings.ROOT_URLCONF = "dataportal.urls"

#     # Mock the service factory and service
#     mock_service = MagicMock()
#     mock_get_species_service.return_value = mock_service

#     mock_species = MagicMock()
#     mock_species.model_dump.return_value = {
#         "scientific_name": "Bacteroides uniformis",
#         "common_name": "B. uniformis",
#         "acronym": "BU",
#         "taxonomy_id": 1234,
#     }

#     async def mock_get_species_by_acronym():
#         return mock_species

#     mock_service.get_species_by_acronym = mock_get_species_by_acronym

#     # Test the species genomes endpoint instead of single species
#     response = api_client.get("/api/species/BU/genomes", follow=True)
#     assert response.status_code == 200


# @patch("dataportal.services.service_factory.ServiceFactory.get_genome_service")
# @patch("django.conf.settings")
# def test_genome_by_strain_name_positive(mock_settings, mock_get_genome_service, api_client):
#     # Mock Django settings
#     mock_settings.SESSION_ENGINE = "django.contrib.sessions.backends.db"
#     mock_settings.MIDDLEWARE = []
#     mock_settings.ROOT_URLCONF = "dataportal.urls"

#     # Mock the service factory and service
#     mock_service = MagicMock()
#     mock_get_genome_service.return_value = mock_service

#     mock_genome = MagicMock()
#     mock_genome.model_dump.return_value = {
#         "isolate_name": "BU_ATCC8492",
#         "assembly_name": "ASM001",
#         "type_strain": True,
#         "species_scientific_name": "Bacteroides uniformis",
#         "species_acronym": "BU",
#     }

#     async def mock_get_genome_by_strain_name():
#         return mock_genome

#     mock_service.get_genome_by_strain_name = mock_get_genome_by_strain_name

#     # Test the genome genes endpoint instead of single genome
#     response = api_client.get("/api/genomes/BU_ATCC8492/genes", follow=True)
#     assert response.status_code == 200


# @patch("dataportal.services.service_factory.ServiceFactory.get_gene_service")
# @patch("django.conf.settings")
# def test_gene_by_locus_tag_positive(mock_settings, mock_get_gene_service, api_client):
#     # Mock Django settings
#     mock_settings.SESSION_ENGINE = "django.contrib.sessions.backends.db"
#     mock_settings.MIDDLEWARE = []
#     mock_settings.ROOT_URLCONF = "dataportal.urls"

#     # Mock the service factory and service
#     mock_service = MagicMock()
#     mock_get_gene_service.return_value = mock_service

#     mock_gene = MagicMock()
#     mock_gene.model_dump.return_value = {
#         "locus_tag": "BU_ATCC8492_00001",
#         "gene_name": "dnaA",
#         "isolate_name": "BU_ATCC8492",
#         "species_acronym": "BU",
#     }

#     async def mock_get_gene_by_locus_tag():
#         return mock_gene

#     mock_service.get_gene_by_locus_tag = mock_get_gene_by_locus_tag

#     # Follow redirects to get the actual response
#     response = api_client.get("/api/genes/BU_ATCC8492_00001/", follow=True)
#     assert response.status_code == 200
#     data = response.json()
#     assert data["locus_tag"] == "BU_ATCC8492_00001"
#     assert data["gene_name"] == "dnaA"
