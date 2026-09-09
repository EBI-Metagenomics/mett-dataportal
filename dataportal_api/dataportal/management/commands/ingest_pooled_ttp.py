import logging
from django.core.management.base import BaseCommand
from dataportal.ingest.feature_experiment.pooled_ttp import PooledTTP
from dataportal.utils.constants import INDEX_FEATURES, INDEX_FEATURE_EXPERIMENTS

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")


class Command(BaseCommand):
    help = "Ingest pooled TTP data into feature_experiment_index."

    def add_arguments(self, parser):
        parser.add_argument("--csv-file", required=True, help="Path to the pooled TTP CSV file")
        parser.add_argument("--pool-metadata", help="Path to the pool metadata CSV file (optional)")
        parser.add_argument(
            "--index",
            default=INDEX_FEATURE_EXPERIMENTS,
            help="Target Elasticsearch feature experiment index (default: feature_experiment_index)",
        )
        parser.add_argument(
            "--feature-index",
            default=INDEX_FEATURES,
            help="Feature index for denormalized flags",
        )

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        pool_metadata = options.get("pool_metadata")
        index_name = options["index"]

        self.stdout.write("Starting pooled TTP ingestion...")
        self.stdout.write(f"CSV file: {csv_file}")
        if pool_metadata:
            self.stdout.write(f"Pool metadata: {pool_metadata}")
        self.stdout.write(f"Target index: {index_name}")

        try:
            # Initialize the PooledTTP flow
            ttp_flow = PooledTTP(
                index_name=index_name,
                pool_metadata_path=pool_metadata,
                feature_flag_index=options["feature_index"],
            )

            # Run the ingestion
            processed_count = ttp_flow.run(csv_file)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully ingested {processed_count} pooled TTP records into {index_name}"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during ingestion: {str(e)}"))
            raise
