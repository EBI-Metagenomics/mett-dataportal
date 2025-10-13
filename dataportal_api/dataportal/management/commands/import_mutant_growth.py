"""
Django management command to import mutant growth data.

This command processes CSV files containing mutant growth data (doubling times,
plate positions, etc.) and imports them into the FeatureDocument mutant_growth
nested field.
"""

from django.core.management.base import BaseCommand
from pathlib import Path

from dataportal.ingest.feature.flows.mutant_growth import MutantGrowthFlow
from dataportal.ingest.utils import list_csv_files


class Command(BaseCommand):
    help = "Import mutant growth data from a directory into feature_index"

    def add_arguments(self, parser):
        parser.add_argument(
            "--mutant-growth-dir",
            type=str,
            required=True,
            help="Path to directory containing mutant growth CSV files"
        )
        parser.add_argument(
            "--index",
            default="feature_index",
            help="Elasticsearch index name (default: feature_index)"
        )
        parser.add_argument(
            "--media",
            default="caecal",
            help="Media type for the experiment (default: caecal)"
        )
        parser.add_argument(
            "--experimental-condition",
            type=str,
            default=None,
            help="Experimental condition context (default: {media}_growth)"
        )

    def handle(self, *args, **options):
        index = options["index"]
        mutant_growth_dir = options["mutant_growth_dir"]
        media = options["media"]
        experimental_condition = options.get("experimental_condition")

        # Validate directory exists
        if not Path(mutant_growth_dir).exists():
            self.stdout.write(
                self.style.ERROR(f"✗ Directory not found: {mutant_growth_dir}")
            )
            return

        # Get all CSV files from directory
        files = list_csv_files(mutant_growth_dir)

        if not files:
            self.stdout.write(
                self.style.WARNING(f"⚠ No CSV files found in: {mutant_growth_dir}")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"[import_mutant_growth] Found {len(files)} CSV file(s) in {mutant_growth_dir}"
            )
        )

        # Create flow instance
        flow = MutantGrowthFlow(
            index_name=index,
            media=media,
            experimental_condition=experimental_condition
        )

        # Process each file
        success_count = 0
        error_count = 0

        for csv_path in files:
            filename = Path(csv_path).name
            self.stdout.write(f"\n  Processing: {filename}")
            try:
                flow.run(csv_path)
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"    ✓ Successfully imported: {filename}")
                )
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"    ✗ Error processing {filename}: {e}")
                )
                import traceback
                if options.get('verbosity', 1) >= 2:
                    self.stdout.write(traceback.format_exc())

        # Summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(
            self.style.SUCCESS(
                f"[import_mutant_growth] Completed!\n"
                f"  Total files: {len(files)}\n"
                f"  Successful: {success_count}\n"
                f"  Failed: {error_count}\n"
                f"  Media: {media}\n"
                f"  Experimental condition: {flow.experimental_condition}"
            )
        )
        self.stdout.write("="*60)
