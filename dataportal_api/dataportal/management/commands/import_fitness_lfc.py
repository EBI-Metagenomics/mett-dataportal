"""
Management command to import gene fitness LFC (Log Fold Change) data.

This command imports fitness data from CSV files into gene_experiment_index.
"""

from django.core.management.base import BaseCommand
from pathlib import Path
from dataportal.ingest.gene_experiment.fitness import Fitness
from dataportal.ingest.utils import list_csv_files
from dataportal.utils.constants import INDEX_GENE_EXPERIMENTS


class Command(BaseCommand):
    help = "Import gene fitness LFC data into gene_experiment_index"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fitness-dir",
            type=str,
            required=True,
            help="Path to directory containing fitness LFC CSV files",
        )
        parser.add_argument(
            "--index",
            default=INDEX_GENE_EXPERIMENTS,
            help="Elasticsearch gene experiment index (default: gene_experiment_index)",
        )
        parser.add_argument(
            "--feature-index",
            default="feature_index",
            help="Feature index for denormalized has_fitness flags",
        )

    def handle(self, *args, **options):
        index = options["index"]
        fitness_dir = options["fitness_dir"]

        # Validate directory exists
        if not Path(fitness_dir).exists():
            self.stdout.write(self.style.ERROR(f"✗ Directory not found: {fitness_dir}"))
            return

        # Get all CSV files from directory
        files = list_csv_files(fitness_dir)

        if not files:
            self.stdout.write(self.style.WARNING(f"⚠ No CSV files found in: {fitness_dir}"))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"[import_fitness_lfc] Found {len(files)} CSV file(s) in {fitness_dir}"
            )
        )

        # Create flow instance
        flow = Fitness(index_name=index, feature_flag_index=options["feature_index"])

        # Process each file
        success_count = 0
        error_count = 0

        for csv_path in files:
            filename = Path(csv_path).name
            self.stdout.write(f"\n  Processing: {filename}")
            try:
                flow.run(csv_path)
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f"    ✓ Successfully imported: {filename}"))
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"    ✗ Error processing {filename}: {e}"))
                import traceback

                if options.get("verbosity", 1) >= 2:
                    self.stdout.write(traceback.format_exc())

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f"[import_fitness_lfc] Completed!\n"
                f"  Total files: {len(files)}\n"
                f"  Successful: {success_count}\n"
                f"  Failed: {error_count}"
            )
        )
        self.stdout.write("=" * 60)
