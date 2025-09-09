from django.core.management.base import BaseCommand
from elasticsearch_dsl import connections

from dataportal.ingest.es_repo import PPIIndexRepository
from dataportal.ingest.ppi import PPICSVFlow

SPECIES_MAP = {"Bacteroides uniformis": "BU"}  # extend as needed


class Command(BaseCommand):
    help = "Import PPI CSVs into Elasticsearch"

    def add_arguments(self, parser):
        parser.add_argument("--index", required=True, help="Target ES index or write alias (e.g., ppi_index_v3)")
        parser.add_argument("--dir", required=True, help="Folder with PPI CSV files")
        parser.add_argument("--pattern", default="*.csv", help="Glob pattern (default: *.csv)")
        parser.add_argument("--batch-size", type=int, default=10000)
        parser.add_argument("--refresh-every-rows", type=int, default=None)
        parser.add_argument("--refresh-every-secs", type=int, default=None)

    def handle(self, *args, **opts):
        es = connections.get_connection()  # use your configured DSL connection
        repo = PPIIndexRepository(
            concrete_index=opts["index"],
            client=es,
        )

        flow = PPICSVFlow(repo=repo, species_map=SPECIES_MAP)
        count = flow.run(folder=opts["dir"], pattern=opts["pattern"], batch_size=opts["batch_size"])
        self.stdout.write(self.style.SUCCESS(
            f"Indexed/updated {count} PPI documents into '{opts['index']}'."
        ))
