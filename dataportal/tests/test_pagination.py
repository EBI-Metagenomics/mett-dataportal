from django.urls import reverse
from .test_setup import BaseTestSetup

class PaginationTest(BaseTestSetup):

    def test_pagination_first_page(self):
        response = self.client.get(reverse('search'), {'query': 'Bacteroides uniformis', 'page': 1, 'page_size': 2})
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 2)  # Should return first 2 results

    def test_pagination_second_page(self):
        response = self.client.get(reverse('search'), {'query': 'Bacteroides uniformis', 'page': 2, 'page_size': 2})
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)  # Should return the remaining result
