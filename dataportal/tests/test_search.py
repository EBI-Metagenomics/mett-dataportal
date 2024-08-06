from django.test import TestCase
from django.urls import reverse
from dataportal.models import SpeciesData

class SearchFunctionalityTest(TestCase):

    def setUp(self):
        # Set up data for the whole TestCase
        self.species1 = SpeciesData.objects.create(
            species="Bacteroides uniformis",
            isolate_name="BU_2243B",
            assembly_name="BU_2243B_NT5389.1",
            fasta_file="http://example.com/fasta1",
            gff_file="http://example.com/gff1"
        )
        self.species2 = SpeciesData.objects.create(
            species="Escherichia coli",
            isolate_name="EC_1234",
            assembly_name="EC_1234_NT1234.1",
            fasta_file="http://example.com/fasta2",
            gff_file="http://example.com/gff2"
        )

    def test_search_species(self):
        response = self.client.get(reverse('search_results'), {'query': 'Bacteroides'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bacteroides uniformis')

    def test_search_isolate(self):
        response = self.client.get(reverse('search_results'), {'query': 'BU_2243B'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'BU_2243B')

    def test_search_no_results(self):
        response = self.client.get(reverse('search_results'), {'query': 'NonExistentSpecies'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Bacteroides uniformis')
        self.assertNotContains(response, 'Escherichia coli')

    def test_search_pagination(self):
        response = self.client.get(reverse('search_results'), {'query': 'Bacteroides', 'page': 1})
        self.assertEqual(response.status_code, 200)
        # Check if pagination exists in the response
        self.assertContains(response, 'pagination')

    def test_search_case_insensitive(self):
        response = self.client.get(reverse('search_results'), {'query': 'bacteroides'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bacteroides uniformis')

    def test_search_partial_match(self):
        response = self.client.get(reverse('search_results'), {'query': 'Bact'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bacteroides uniformis')

