from django.core.management.base import BaseCommand
from dataportal.utils import create_full_text_search_table, update_full_text_search

class Command(BaseCommand):
    help = 'Initialize the FTS5 table'

    def handle(self, *args, **kwargs):
        create_full_text_search_table()
        update_full_text_search()
        self.stdout.write(self.style.SUCCESS('FTS5 table initialized successfully.'))
