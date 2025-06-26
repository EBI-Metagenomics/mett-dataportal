import pytest
from django.test import Client
from unittest.mock import MagicMock, patch


@pytest.fixture
def api_client():
    return Client()


@patch("dataportal.services.species_service.sync_to_async")
def test_species_list_positive(mock_sync_to_async, api_client):
    mock_doc1 = MagicMock()
    mock_doc1.to_dict.return_value = {
        "scientific_name": "Bacteroides uniformis",
        "common_name": "B. uniformis",
        "acronym": "BU",
        "taxonomy_id": 1234,
    }
    mock_doc2 = MagicMock()
    mock_doc2.to_dict.return_value = {
        "scientific_name": "Phocaeicola vulgatus",
        "common_name": "P. vulgatus",
        "acronym": "PV",
        "taxonomy_id": 5678,
    }

    async def mock_execute():
        return [mock_doc1, mock_doc2]

    mock_sync_to_async.return_value = mock_execute

    response = api_client.get("/api/species/")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["scientific_name"] == "Bacteroides uniformis"


@patch("dataportal.services.species_service.sync_to_async")
def test_species_list_empty(mock_sync_to_async, api_client):
    async def mock_execute():
        return []

    mock_sync_to_async.return_value = mock_execute

    response = api_client.get("/api/species/")
    assert response.status_code == 200
    assert response.json() == []
