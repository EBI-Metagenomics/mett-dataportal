from django.core.management.base import BaseCommand
from dataportal.models import Species
import pandas as pd


class Command(BaseCommand):
    help = "Imports species data from a CSV file into the Species model."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            type=str,
            help="Path to the CSV file containing species data",
            default="./species.csv",
        )

    def handle(self, *args, **kwargs):
        csv_path = kwargs["csv"]
        self.stdout.write(f"Loading data from {csv_path}")

        # Load the CSV data into a DataFrame
        species_df = pd.read_csv(csv_path)
        self.stdout.write(f"Species DataFrame: \n{species_df}")

        # Insert data into the Species table
        for row in species_df.itertuples(index=False):
            species, created = Species.objects.get_or_create(
                id=row.id,
                defaults={
                    "scientific_name": row.scientific_name,
                    "common_name": row.common_name,
                    "acronym": row.acronym,
                    "taxonomy_id": row.taxonomy_id,
                },
            )
            if created:
                self.stdout.write(f"Inserted species: {species.scientific_name}")
            else:
                self.stdout.write(f"Species {species.scientific_name} already exists")

        self.stdout.write(
            self.style.SUCCESS("Species data successfully imported into the database.")
        )
