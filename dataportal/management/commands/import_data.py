import csv
from django.core.management.base import BaseCommand
from dataportal.models import SpeciesData
from dataportal.utils.fts_utils import FullTextSearchManager
import os


class Command(BaseCommand):
    help = 'Import species data from CSV'

    def handle(self, *args, **kwargs):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_file_path = os.path.join(base_dir, '../../data/assemblies_annotations_map.csv')

        with open(data_file_path, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            for row in reader:
                SpeciesData.objects.create(
                    species=row[0],
                    isolate_name=row[1],
                    assembly_name=row[2],
                    fasta_file=row[3],
                    gff_file=row[4]
                )

        fts_manager = FullTextSearchManager(
            table_name='speciesdata',
            fields=['species', 'isolate_name', 'assembly_name', 'fasta_file', 'gff_file']
        )
        fts_manager.update_full_text_search()
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))
