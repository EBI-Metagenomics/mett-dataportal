from django.core.management.base import BaseCommand, CommandError
from elasticsearch.helpers import BulkIndexError
from elasticsearch_dsl import connections

from dataportal.ingest.species.importer import ingest_species


class Command(BaseCommand):
    help = "Imports species data from a CSV file into a specified Elasticsearch index."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            type=str,
            default="../data-generators/data/species.csv",
            help="Path to the CSV file containing species data",
        )
        parser.add_argument(
            "--index",
            type=str,
            required=True,
            help="Target Elasticsearch index name (e.g. species_v3)",
        )
        parser.add_argument(
            "--refresh",
            action="store_true",
            help="Force refresh after indexing (useful for tests/dev).",
        )

    def handle(self, *args, **options):
        csv_path = options["csv"]
        index_name = options["index"]
        if not index_name:
            raise CommandError("--index is required")

        self.stdout.write(f"Loading species data from {csv_path}")
        client = connections.get_connection()
        try:
            ok, errors, loaded = ingest_species(
                client, csv_path, index_name, refresh=options["refresh"]
            )
        except BulkIndexError as e:
            errs = getattr(e, "errors", [])
            self.stderr.write(
                self.style.ERROR(f"{len(errs)} document(s) failed to index. Showing up to 5:")
            )
            for i, err in enumerate(errs[:5], 1):
                self.stderr.write(self.style.ERROR(f"[{i}] {err}"))
            raise

        self.stdout.write(f"Loaded {loaded} records.")
        self.stdout.write(self.style.SUCCESS(f"Indexed {ok} records into '{index_name}'"))
        if errors:
            self.stdout.write(self.style.WARNING(f"Bulk completed with {len(errors)} errors."))
