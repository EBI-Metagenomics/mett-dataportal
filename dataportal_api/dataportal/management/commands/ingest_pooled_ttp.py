import logging
from django.core.management.base import BaseCommand
from dataportal.ingest.feature.flows.pooled_ttp import PooledTTP

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")


class Command(BaseCommand):
    help = "Ingest pooled TTP (Thermal Proteome Profiling) data into the feature index."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv-file",
            required=True,
            help="Path to the pooled TTP CSV file"
        )
        parser.add_argument(
            "--pool-metadata",
            help="Path to the pool metadata CSV file (optional)"
        )
        parser.add_argument(
            "--index",
            default="feature_index",
            help="Target Elasticsearch index name (default: feature_index)"
        )

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        pool_metadata = options.get("pool_metadata")
        index_name = options["index"]
        
        self.stdout.write(f"Starting pooled TTP ingestion...")
        self.stdout.write(f"CSV file: {csv_file}")
        if pool_metadata:
            self.stdout.write(f"Pool metadata: {pool_metadata}")
        self.stdout.write(f"Target index: {index_name}")
        
        try:
            # Initialize the PooledTTP flow
            ttp_flow = PooledTTP(index_name=index_name, pool_metadata_path=pool_metadata)
            
            # Run the ingestion
            processed_count = ttp_flow.run(csv_file)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully ingested {processed_count} pooled TTP records into {index_name}"
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error during ingestion: {str(e)}")
            )
            raise
