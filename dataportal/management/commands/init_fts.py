from django.core.management.base import BaseCommand
from dataportal.utils.fts_utils import FullTextSearchManager


class Command(BaseCommand):
    help = "Initialize full-text search tables"

    def handle(self, *args, **kwargs):
        # Initialize full-text search for Species
        species_fts_manager = FullTextSearchManager(
            table_name="species", fields=["scientific_name", "common_name"]
        )
        species_fts_manager.create_full_text_search_table()

        # Initialize full-text search for Strain
        strain_fts_manager = FullTextSearchManager(
            table_name="strain",
            fields=[
                "isolate_name",
                "strain_name",
                "assembly_name",
                "assembly_accession",
                "fasta_file",
                "gff_file",
            ],
        )
        strain_fts_manager.create_full_text_search_table()

        # Initialize full-text search for Gene
        gene_fts_manager = FullTextSearchManager(
            table_name="gene",
            fields=["gene_id", "gene_name", "gene_symbol", "locus_tag"],
        )
        gene_fts_manager.create_full_text_search_table()

        self.stdout.write(
            self.style.SUCCESS("Full-text search tables initialized successfully")
        )
