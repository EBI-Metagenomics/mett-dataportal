from django.urls import reverse
from .test_setup import BaseTestSetup

class SearchTest(BaseTestSetup):

    def test_search_bacteroides(self):
        response = self.client.get(reverse('search'), {'query': 'Bacteroides uniformis'})
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 3)  # Ensure we get all Bacteroides uniformis entries

    def test_search_phocaeicola(self):
        response = self.client.get(reverse('search'), {'query': 'Phocaeicola vulgatus'})
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 3)  # Ensure we get all Phocaeicola vulgatus entries

    def test_search_no_results(self):
        response = self.client.get(reverse('search'), {'query': 'unknown species'})
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(results, [])
