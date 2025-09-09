from django.core.management.base import BaseCommand
from elasticsearch_dsl import connections

from dataportal.ingest.constants import SPECIES_BY_NAME
from dataportal.ingest.es_repo import PPIIndexRepository
from dataportal.ingest.ppi import PPICSVFlow


class Command(BaseCommand):
    help = "Import PPI CSVs into Elasticsearch"

    def add_arguments(self, parser):
        parser.add_argument("--dir", required=True)
        parser.add_argument("--pattern", default="*.csv")
        parser.add_argument("--batch-size", type=int, default=2000)

    def handle(self, *args, **opts):
        es = connections.get_connection()  # <-- use existing DSL connection
        repo = PPIIndexRepository(concrete_index="ppi_index", client=es)

        flow = PPICSVFlow(repo=repo, species_map=SPECIES_BY_NAME)
        count = flow.run(folder=opts["dir"], pattern=opts["pattern"], batch_size=opts["batch_size"])
        self.stdout.write(self.style.SUCCESS(f"Indexed/updated {count} PPI documents."))
