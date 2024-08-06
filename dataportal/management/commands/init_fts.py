from django.core.management.base import BaseCommand
from dataportal.utils.fts_utils import FullTextSearchManager


class Command(BaseCommand):
    help = 'Initialize full-text search table'

    def handle(self, *args, **kwargs):
        fts_manager = FullTextSearchManager(
            table_name='speciesdata',
            fields=['species', 'isolate_name', 'assembly_name', 'fasta_file', 'gff_file']
        )
        fts_manager.create_full_text_search_table()
        self.stdout.write(self.style.SUCCESS('Full-text search table initialized successfully'))
