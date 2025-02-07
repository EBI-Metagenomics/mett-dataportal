from django.core.management.base import BaseCommand
from dataportal.elasticsearch.indexing import create_index


class Command(BaseCommand):
    help = "Creates Elasticsearch indexes"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting Elasticsearch index creation..."))
        create_index()
        self.stdout.write(self.style.SUCCESS("Elasticsearch index creation completed."))
