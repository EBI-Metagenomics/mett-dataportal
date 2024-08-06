from django.urls import reverse
from .test_setup import BaseTestSetup

class AssemblyFilePathTest(BaseTestSetup):

    def test_assembly_file_path(self):
        response = self.client.get(reverse('search'), {'query': 'BU_2243B'})
        self.assertEqual(response.status_code, 200)
        result = response.json()['results'][0]
        print(f'result: {result}')
        self.assertEqual(result['fasta_file'], 'BU_2243B_NT5389.1.fa')
