from django.urls import reverse
from .test_setup import BaseTestSetup

class AutocompleteTest(BaseTestSetup):

    def test_autocomplete_bacteroides(self):
        response = self.client.get(reverse('autocomplete'), {'query': 'Bac'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.json()['suggestions']
        self.assertIn("Bacteroides uniformis", suggestions)

    def test_autocomplete_phocaeicola(self):
        response = self.client.get(reverse('autocomplete'), {'query': 'Pho'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.json()['suggestions']
        self.assertIn("Phocaeicola vulgatus", suggestions)

    def test_autocomplete_no_results(self):
        response = self.client.get(reverse('autocomplete'), {'query': 'unknown'})
        self.assertEqual(response.status_code, 200)
        suggestions = response.json()['suggestions']
        self.assertEqual(suggestions, [])
