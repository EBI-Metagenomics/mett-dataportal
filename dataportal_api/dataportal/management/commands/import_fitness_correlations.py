"""
Management command to import gene-gene fitness correlation data.

This command imports fitness correlation matrices from CSV files in a directory
into the GeneFitnessCorrelationDocument Elasticsearch index.
"""

from django.core.management.base import BaseCommand
from pathlib import Path
from dataportal.ingest.feature.flows.fitness_correlation import FitnessCorrelationFlow
from dataportal.ingest.es_repo import GeneFitnessCorrelationIndexRepository
from dataportal.ingest.gff.parser import GFFParser
from dataportal.ingest.utils import list_csv_files


class Command(BaseCommand):
    help = "Import gene-gene fitness correlation data from a directory into fitness_correlation_index"

    def add_arguments(self, parser):
        parser.add_argument(
            "--correlation-dir",
            type=str,
            required=True,
            help="Path to directory containing correlation CSV files (Gene-Gene matrices)"
        )
        parser.add_argument(
            "--index",
            default="fitness_correlation_index",
            help="Elasticsearch index name (default: fitness_correlation_index)"
        )
        parser.add_argument(
            "--preload-gff",
            action="store_true",
            help="Preload GFF files to enrich with gene information"
        )
        parser.add_argument(
            "--ftp-server",
            type=str,
            default="ftp.ebi.ac.uk",
            help="FTP server for GFF files (default: ftp.ebi.ac.uk)"
        )
        parser.add_argument(
            "--ftp-directory",
            type=str,
            default="/pub/databases/mett/annotations/v1_2024-04-15/",
            help="FTP directory for GFF files (default: /pub/databases/mett/annotations/v1_2024-04-15/)"
        )
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=20000,
            help="Number of rows to process at a time (default: 20000, optimized for large datasets)"
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=5000,
            help="Number of documents to index in each batch (default: 5000, optimized for large datasets)"
        )

    def handle(self, *args, **options):
        index = options["index"]
        correlation_dir = options["correlation_dir"]
        
        # Validate directory exists
        if not Path(correlation_dir).exists():
            self.stdout.write(
                self.style.ERROR(f"✗ Directory not found: {correlation_dir}")
            )
            return
        
        # Get all CSV files from directory
        files = list_csv_files(correlation_dir)
        
        if not files:
            self.stdout.write(
                self.style.WARNING(f"⚠ No CSV files found in: {correlation_dir}")
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(
                f"[import_fitness_correlations] Found {len(files)} CSV file(s) in {correlation_dir}"
            )
        )
        
        # Set up GFF parser if requested
        gff_parser = None
        if options.get("preload_gff"):
            self.stdout.write("\n  Initializing GFF parser...")
            self.stdout.write(f"    FTP Server: {options['ftp_server']}")
            self.stdout.write(f"    FTP Directory: {options['ftp_directory']}")
            
            gff_parser = GFFParser(
                ftp_server=options["ftp_server"],
                ftp_directory=options["ftp_directory"],
            )
            
            # Infer species from file names or locus tags
            # For now, manually specify common species
            species_isolate_map = {
                "Bacteroides uniformis": "BU_ATCC8492",
                "Prevotella vulgatus": "PV_ATCC8482",
            }
            
            self.stdout.write(f"    Species mapping: {species_isolate_map}")
            gff_parser.set_species_mapping(species_isolate_map)
            gff_parser.preload_gff_files(list(species_isolate_map.keys()))
            self.stdout.write(self.style.SUCCESS("  ✓ GFF files preloaded"))
        
        # Create repository and flow
        repo = GeneFitnessCorrelationIndexRepository(concrete_index=index)
        flow = FitnessCorrelationFlow(
            repo=repo,
            gff_parser=gff_parser,
            chunk_size=options["chunk_size"],
            batch_size=options["batch_size"],
        )
        
        # Process each file
        total_processed = 0
        total_indexed = 0
        success_count = 0
        error_count = 0
        
        for csv_path in files:
            filename = Path(csv_path).name
            self.stdout.write(f"\n  Processing: {filename}")
            try:
                processed, indexed = flow.run(csv_path)
                total_processed += processed
                total_indexed += indexed
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"    ✓ Processed {processed} rows, indexed {indexed} correlations"
                    )
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
                f"[import_fitness_correlations] Completed!\n"
                f"  Total files: {len(files)}\n"
                f"  Successful: {success_count}\n"
                f"  Failed: {error_count}\n"
                f"  Total rows processed: {total_processed}\n"
                f"  Total correlations indexed: {total_indexed}"
            )
        )
        self.stdout.write("="*60)

