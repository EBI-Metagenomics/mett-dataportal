from django.urls import reverse
from .test_setup import BaseTestSetup

class GFFFilePathTest(BaseTestSetup):

    def test_gff_file_path(self):
        response = self.client.get(reverse('search'), {'query': 'PV_H4-2'})
        self.assertEqual(response.status_code, 200)
        result = response.json()['results'][0]
        self.assertEqual(result['gff_file'], 'PV_H4-2_annotations.gff')
