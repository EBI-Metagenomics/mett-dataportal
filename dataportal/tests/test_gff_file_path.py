import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_gff_file_path(client, fts_setup):
    response = client.get(reverse('search'), {'query': 'PV_H4-2'})
    print(response.content)
    assert response.status_code == 200
    result = response.json()['results'][0]
    assert result['gff_file'] == 'PV_H4-2_annotations.gff'
