import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_assembly_file_path(client, fts_setup):
    response = client.get(reverse('search'), {'query': 'BU_2243B'})
    print(response.content)
    assert response.status_code == 200
    result = response.json()['results'][0]
    assert result['fasta_file'] == 'BU_2243B_NT5389.1.fa'
