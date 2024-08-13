import csv
import os
from django.core.management.base import BaseCommand
from dataportal.models import Species, Strain, Gene
from dataportal.utils.fts_utils import FullTextSearchManager


class Command(BaseCommand):
    help = 'Import species, strain, and gene data from CSV files'

    def handle(self, *args, **kwargs):
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Paths to the CSV files
        species_file_path = os.path.join(base_dir, '../../data/species.csv')
        strain_file_path = os.path.join(base_dir, '../../data/strain.csv')
        gene_file_path = os.path.join(base_dir, '../../data/gene.csv')

        # Import Species Data
        with open(species_file_path, 'r') as species_file:
            species_reader = csv.reader(species_file)
            next(species_reader)  # Skip header row
            for row in species_reader:
                Species.objects.create(
                    scientific_name=row[0],
                    common_name=row[1],
                    taxonomy_id=row[2]
                )
        self.stdout.write(self.style.SUCCESS('Species data imported successfully'))

        # Import Strain Data
        with open(strain_file_path, 'r') as strain_file:
            strain_reader = csv.reader(strain_file)
            next(strain_reader)  # Skip header row
            for row in strain_reader:
                species = Species.objects.get(id=row[0])  # Get the related Species
                Strain.objects.create(
                    species=species,
                    isolate_name=row[1],
                    strain_name=row[2],
                    assembly_name=row[3],
                    fasta_file=row[4],
                    gff_file=row[5],
                    assembly_accession=row[6]
                )
        self.stdout.write(self.style.SUCCESS('Strain data imported successfully'))

        # Import Gene Data
        with open(gene_file_path, 'r') as gene_file:
            gene_reader = csv.reader(gene_file)
            next(gene_reader)  # Skip header row
            for row in gene_reader:
                strain = Strain.objects.get(id=row[0])  # Get the related Strain
                Gene.objects.create(
                    strain=strain,
                    gene_id=row[1],
                    gene_name=row[2],
                    gene_symbol=row[3],
                    locus_tag=row[4]
                )
        self.stdout.write(self.style.SUCCESS('Gene data imported successfully'))

        # Update Full-Text Search for Species, Strain, and Gene tables if needed
        species_fts_manager = FullTextSearchManager(
            table_name='species',
            fields=['scientific_name', 'common_name']
        )
        species_fts_manager.update_full_text_search()

        strain_fts_manager = FullTextSearchManager(
            table_name='strain',
            fields=['isolate_name', 'strain_name', 'assembly_name', 'fasta_file', 'gff_file']
        )
        strain_fts_manager.update_full_text_search()

        gene_fts_manager = FullTextSearchManager(
            table_name='gene',
            fields=['gene_id', 'gene_name', 'gene_symbol', 'locus_tag']
        )
        gene_fts_manager.update_full_text_search()

        self.stdout.write(self.style.SUCCESS('Full-text search updated successfully'))
