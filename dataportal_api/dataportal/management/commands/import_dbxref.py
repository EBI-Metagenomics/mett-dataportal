"""
Management command to import external database cross-references (dbxref) into feature index.

This command can be used to append external database identifiers (e.g., STRING DB IDs)
to the dbxref attribute of feature documents. It's designed to be extensible for
future external database mappings.

Usage:
    python manage.py import_dbxref --index feature_index_v1 --tsv /path/to/mappings.tsv --db-name STRING
    python manage.py import_dbxref --index feature_index_v1 --tsv-dir /path/to/tsv/files --db-name STRING
"""

from django.core.management.base import BaseCommand, CommandError

from dataportal.ingest.feature.flows.external_dbxref import ExternalDBXRef
from dataportal.ingest.utils import list_csv_files


class Command(BaseCommand):
    help = "Import external database cross-references (dbxref) into feature index."

    def add_arguments(self, parser):
        parser.add_argument(
            "--index",
            type=str,
            required=True,
            help="Target Elasticsearch index name (e.g., feature_index_v1)",
        )
        parser.add_argument(
            "--tsv",
            type=str,
            help="Path to a single TSV file with mappings (locus_tag, external_db_id)",
        )
        parser.add_argument(
            "--tsv-dir",
            type=str,
            help="Directory containing TSV files with mappings",
        )
        parser.add_argument(
            "--db-name",
            type=str,
            default="STRING",
            help="Name of the external database (default: STRING). Examples: STRING, UniProt, etc.",
        )

    def handle(self, *args, **options):
        index_name = options["index"]
        db_name = options["db_name"]
        tsv_path = options.get("tsv")
        tsv_dir = options.get("tsv_dir")

        if not tsv_path and not tsv_dir:
            raise CommandError("Either --tsv or --tsv-dir must be provided")

        if tsv_path and tsv_dir:
            raise CommandError("Cannot specify both --tsv and --tsv-dir")

        # Initialize the flow
        flow = ExternalDBXRef(index_name=index_name, db_name=db_name)

        # Process single file or directory
        if tsv_path:
            self.stdout.write(self.style.SUCCESS(f"Processing single TSV file: {tsv_path}"))
            flow.run(tsv_path)
        else:
            tsv_files = list_csv_files(tsv_dir, exts=(".tsv", ".tab"))
            if not tsv_files:
                self.stdout.write(self.style.WARNING(f"No TSV files found in directory: {tsv_dir}"))
                return

            self.stdout.write(
                self.style.SUCCESS(
                    f"Processing {len(tsv_files)} TSV files from directory: {tsv_dir}"
                )
            )
            for tsv_file in tsv_files:
                self.stdout.write(f"  - Processing: {tsv_file}")
                flow.run(tsv_file)

        self.stdout.write(
            self.style.SUCCESS(
                f"Completed importing dbxref for database '{db_name}' into index '{index_name}'"
            )
        )
