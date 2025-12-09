import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from elasticsearch_dsl import connections
from elasticsearch.helpers import bulk, BulkIndexError


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
        client = connections.get_connection()

        if not index_name:
            raise CommandError("--index is required")

        self.stdout.write(f"Loading species data from {csv_path}")
        species_df = pd.read_csv(
            csv_path,
            dtype={"scientific_name": "string", "common_name": "string", "acronym": "string"},
        )
        if "taxonomy_id" in species_df.columns:
            species_df["taxonomy_id"] = pd.to_numeric(
                species_df["taxonomy_id"], errors="coerce"
            ).astype("Int64")
        # Handle enabled field - default to True if not present or if value is invalid
        if "enabled" in species_df.columns:
            species_df["enabled"] = (
                pd.to_numeric(species_df["enabled"], errors="coerce").fillna(1).astype(bool)
            )
        else:
            species_df["enabled"] = True
        for col in ("scientific_name", "common_name", "acronym"):
            if col in species_df.columns:
                species_df[col] = species_df[col].fillna("").str.strip()

        self.stdout.write(f"Loaded {len(species_df)} records.")

        def actions():
            for row in species_df.itertuples(index=False):
                src = {
                    "scientific_name": getattr(row, "scientific_name", "") or "",
                    "common_name": getattr(row, "common_name", "") or "",
                    "acronym": getattr(row, "acronym", "") or "",
                }
                tax = getattr(row, "taxonomy_id", None)
                if tax is not None and pd.notna(tax):
                    src["taxonomy_id"] = int(tax)

                # Handle enabled field - default to True if not present
                enabled = getattr(row, "enabled", True)
                if enabled is None or pd.isna(enabled):
                    enabled = True
                src["enabled"] = bool(enabled)

                yield {
                    "_op_type": "index",
                    "_index": index_name,
                    "_id": src["acronym"] or None,
                    "_source": src,
                }

        try:
            ok, errors = bulk(
                client,
                actions(),
                chunk_size=2000,
                request_timeout=120,
                refresh="wait_for" if options["refresh"] else False,
            )
            self.stdout.write(self.style.SUCCESS(f"Indexed {ok} records into '{index_name}'"))
            if errors:
                self.stdout.write(self.style.WARNING(f"Bulk completed with {len(errors)} errors."))
        except BulkIndexError as e:
            errs = getattr(e, "errors", [])
            self.stderr.write(
                self.style.ERROR(f"{len(errs)} document(s) failed to index. Showing up to 5:")
            )
            for i, err in enumerate(errs[:5], 1):
                self.stderr.write(self.style.ERROR(f"[{i}] {err}"))
            raise
