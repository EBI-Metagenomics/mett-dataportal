import os
import pandas as pd
from django.core.management.base import BaseCommand
from elasticsearch_dsl import connections
from elasticsearch.helpers import bulk
from dataportal.elasticsearch.models import SpeciesDocument

# Load environment variables for Elasticsearch
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_USER = os.getenv("ES_USER")
ES_PASSWORD = os.getenv("ES_PASSWORD")

# Establish Elasticsearch connection
connections.create_connection(hosts=[ES_HOST], http_auth=(ES_USER, ES_PASSWORD))

class Command(BaseCommand):
    help = "Imports species data from a CSV file into Elasticsearch using elasticsearch-dsl."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            type=str,
            help="Path to the CSV file containing species data",
            default="../data-generators/data/species.csv",
        )

    def handle(self, *args, **options):
        csv_path = options["csv"]
        self.stdout.write(f"Loading species data from {csv_path}")

        # Load the CSV data into a DataFrame
        species_df = pd.read_csv(csv_path)
        self.stdout.write(f"Loaded {len(species_df)} records.")

        # Prepare documents for bulk indexing
        species_docs = [
            SpeciesDocument(
                meta={"id": row.acronym},
                scientific_name=row.scientific_name,
                common_name=row.common_name if pd.notna(row.common_name) else "",
                acronym=row.acronym if pd.notna(row.acronym) else "",
                taxonomy_id=row.taxonomy_id
            )
            for row in species_df.itertuples(index=False)
        ]

        # Bulk index species data
        if species_docs:
            bulk(connections.get_connection(), (doc.to_dict(include_meta=True) for doc in species_docs))
            self.stdout.write(self.style.SUCCESS(f"Successfully indexed {len(species_docs)} species records into Elasticsearch."))
        else:
            self.stdout.write(self.style.WARNING("No records to index."))
