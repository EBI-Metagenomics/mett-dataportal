import csv
from django.core.management.base import BaseCommand
from dataportal.models import SpeciesData
from dataportal.utils import update_full_text_search

class Command(BaseCommand):
    help = 'Import species data from CSV'

    def handle(self, *args, **kwargs):
        with open('./Assemblies-Annotations-Map.csv', 'r') as file:
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
        update_full_text_search()
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))
