from django.core.management.base import BaseCommand
from dataportal.elasticsearch.indexing import create_indexes


class Command(BaseCommand):
    help = "Creates Elasticsearch indexes"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting Elasticsearch index creation..."))
        create_indexes()
        self.stdout.write(self.style.SUCCESS("Elasticsearch index creation completed."))
