import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_autocomplete_bacteroides(client, fts_setup):
    response = client.get(reverse('autocomplete'), {'query': 'Bac'})
    print(response.content)
    assert response.status_code == 200
    suggestions = response.json()['suggestions']
    assert "Bacteroides uniformis - BU_2243B (BU_2243B_NT5389.1)" in suggestions
    assert "Bacteroides uniformis - BU_3537 (BU_3537_NT5405.1)" in suggestions
    assert "Bacteroides uniformis - BU_61 (BU_61_NT5381.1)" in suggestions

@pytest.mark.django_db
def test_autocomplete_phocaeicola(client, fts_setup):
    response = client.get(reverse('autocomplete'), {'query': 'Pho'})
    print(response.content)
    assert response.status_code == 200
    suggestions = response.json()['suggestions']
    assert "Phocaeicola vulgatus - PV_H4-2 (PV_H42_NT5107.1)" in suggestions
    assert "Phocaeicola vulgatus - PV_H5-1 (PV_H51_NT5108.1)" in suggestions
    assert "Phocaeicola vulgatus - PV_H6-5 (PV_H65_NT5109.1)" in suggestions

@pytest.mark.django_db
def test_autocomplete_no_results(client, fts_setup):
    response = client.get(reverse('autocomplete'), {'query': 'unknown'})
    print(response.content)
    assert response.status_code == 200
    suggestions = response.json()['suggestions']
    assert suggestions == []
