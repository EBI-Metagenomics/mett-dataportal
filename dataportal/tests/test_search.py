import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_search_bacteroides(client, fts_setup):
    response = client.get(reverse('search'), {'query': 'Bacteroides uniformis'})
    print(response.content)
    assert response.status_code == 200
    results = response.json()['results']
    assert any('Bacteroides uniformis' in result['species'] for result in results)

@pytest.mark.django_db
def test_search_phocaeicola(client, fts_setup):
    response = client.get(reverse('search'), {'query': 'Phocaeicola vulgatus'})
    print(response.content)
    assert response.status_code == 200
    results = response.json()['results']
    assert any('Phocaeicola vulgatus' in result['species'] for result in results)

@pytest.mark.django_db
def test_search_no_results(client, fts_setup):
    response = client.get(reverse('search'), {'query': 'unknown species'})
    print(response.content)
    assert response.status_code == 200
    results = response.json()['results']
    assert len(results) == 0
