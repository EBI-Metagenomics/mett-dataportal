from django.urls import reverse
from .test_setup import BaseTestSetup
import logging

logger = logging.getLogger(__name__)

class SearchTest(BaseTestSetup):

    def test_search_bacteroides(self):
        logger.info("Running test_search_bacteroides")
        response = self.client.get(reverse('search'), {'query': 'Bacteroides uniformis'})
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 3)  # Ensure we get all Bacteroides uniformis entries

    def test_search_phocaeicola(self):
        logger.info("Running test_search_phocaeicola")
        response = self.client.get(reverse('search'), {'query': 'Phocaeicola vulgatus'})
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 3)  # Ensure we get all Phocaeicola vulgatus entries

    def test_search_no_results(self):
        logger.info("Running test_search_no_results")
        response = self.client.get(reverse('search'), {'query': 'unknown species'})
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(results, [])
