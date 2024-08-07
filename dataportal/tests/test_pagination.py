import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_pagination_first_page(client, fts_setup):
    response = client.get(reverse('search'), {'query': 'Bacteroides uniformis', 'page': 1, 'page_size': 2})
    print(response.content)
    assert response.status_code == 200
    results = response.json()['results']
    assert len(results) == 2  # Should return first 2 results

@pytest.mark.django_db
def test_pagination_second_page(client, fts_setup):
    response = client.get(reverse('search'), {'query': 'Bacteroides uniformis', 'page': 2, 'page_size': 2})
    print(response.content)
    assert response.status_code == 200
    results = response.json()['results']
    assert len(results) == 1  # Should return the remaining result
