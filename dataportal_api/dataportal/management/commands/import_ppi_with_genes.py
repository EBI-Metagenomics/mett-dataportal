"""
Management command to import PPI data with gene information from GFF files.

This command extends the existing PPI import functionality to include gene information
extracted from GFF files, with in-memory caching to avoid re-downloading the same files.
"""

import os
import logging
from django.core.management.base import BaseCommand, CommandError
from dataportal.ingest.ppi.gff_parser import GFFParser
from dataportal.ingest.ppi.flows.ppi_csv import PPICSVFlow
from dataportal.ingest.es_repo import PPIIndexRepository

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import PPI data with gene information from GFF files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv-folder",
            type=str,
            required=True,
            help="Path to folder containing PPI CSV files"
        )
        parser.add_argument(
            "--pattern",
            type=str,
            default="*.csv",
            help="File pattern to match CSV files (default: *.csv)"
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
            help="FTP directory for GFF files"
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=5000,
            help="Batch size for indexing (default: 5000)"
        )
        parser.add_argument(
            "--log-every",
            type=int,
            default=100_000,
            help="Log progress every N records (default: 100000)"
        )
        parser.add_argument(
            "--no-gene-info",
            action="store_true",
            help="Skip gene information extraction (faster but no gene data)"
        )
        parser.add_argument(
            "--species-mapping",
            type=str,
            help="Path to species mapping file (optional)"
        )
        parser.add_argument(
            "--index",
            type=str,
            help="Elasticsearch index name (optional, uses default if not specified)"
        )
        parser.add_argument(
            "--refresh",
            type=str,
            choices=["true", "false", "wait_for"],
            help="Refresh policy: true, false, or wait_for (default: wait_for)"
        )
        parser.add_argument(
            "--refresh-every-rows",
            type=int,
            help="Refresh index every N rows (optional)"
        )
        parser.add_argument(
            "--refresh-every-secs",
            type=float,
            help="Refresh index every N seconds (optional)"
        )
        parser.add_argument(
            "--no-optimize-indexing",
            action="store_true",
            help="Disable indexing optimization (slower but uses less memory)"
        )

    def handle(self, *args, **options):
        csv_folder = options["csv_folder"]
        pattern = options["pattern"]
        ftp_server = options["ftp_server"]
        ftp_directory = options["ftp_directory"]
        batch_size = options["batch_size"]
        log_every = options["log_every"]
        no_gene_info = options["no_gene_info"]
        species_mapping_file = options["species_mapping"]
        index_name = options.get("index")
        refresh = options.get("refresh", "wait_for")
        refresh_every_rows = options.get("refresh_every_rows")
        refresh_every_secs = options.get("refresh_every_secs")
        optimize_indexing = not options.get("no_optimize_indexing", False)

        # Validate CSV folder
        if not os.path.exists(csv_folder):
            raise CommandError(f"CSV folder not found: {csv_folder}")

        # Load species mapping
        species_map = self._load_species_mapping(species_mapping_file)

        # Initialize GFF parser if gene information is requested
        gff_parser = None
        if not no_gene_info:
            self.stdout.write("Initializing GFF parser...")
            self.stdout.write(f"FTP Server: {ftp_server}")
            self.stdout.write(f"FTP Directory: {ftp_directory}")
            gff_parser = GFFParser(
                ftp_server=ftp_server,
                ftp_directory=ftp_directory
            )
            self.stdout.write(
                self.style.SUCCESS("GFF parser initialized successfully")
            )
        else:
            self.stdout.write(
                self.style.WARNING("Skipping gene information extraction")
            )

        # Initialize PPI repository
        self.stdout.write("Initializing PPI repository...")
        
        # Use custom index if specified, otherwise use default
        if not index_name:
            index_name = "ppi_index"  # Default index name
        
        repo = PPIIndexRepository(concrete_index=index_name)
        self.stdout.write(f"Using index: {index_name}")

        # Create PPI CSV flow
        flow = PPICSVFlow(
            repo=repo,
            species_map=species_map,
            gff_parser=gff_parser
        )

        # Run the import process
        self.stdout.write(f"Starting PPI import from: {csv_folder}")
        self.stdout.write(f"Pattern: {pattern}")
        self.stdout.write(f"Batch size: {batch_size}")
        self.stdout.write(f"Refresh policy: {refresh}")
        self.stdout.write(f"Gene information: {'Enabled' if gff_parser else 'Disabled'}")
        if gff_parser:
            self.stdout.write(f"FTP Server: {ftp_server}")
            self.stdout.write(f"FTP Directory: {ftp_directory}")
        self.stdout.write(f"Index optimization: {'Enabled' if optimize_indexing else 'Disabled'}")
        
        if refresh_every_rows:
            self.stdout.write(f"Refresh every {refresh_every_rows} rows")
        if refresh_every_secs:
            self.stdout.write(f"Refresh every {refresh_every_secs} seconds")

        try:
            total_indexed = flow.run(
                folder=csv_folder,
                pattern=pattern,
                batch_size=batch_size,
                refresh=refresh,
                log_every=log_every,
                optimize_indexing=optimize_indexing,
                refresh_every_rows=refresh_every_rows,
                refresh_every_secs=refresh_every_secs
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully indexed {total_indexed} PPI records!"
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error during import: {e}")
            )
            raise CommandError(f"Import failed: {e}")

        finally:
            # Clear GFF parser cache
            if gff_parser:
                gff_parser.clear_cache()
                self.stdout.write("GFF parser cache cleared")

    def _load_species_mapping(self, mapping_file):
        """Load species mapping from file or use default."""
        if mapping_file and os.path.exists(mapping_file):
            # Load from file (implement based on your file format)
            # For now, return default mapping
            pass

        # Default species mapping - map to actual isolate names
        return {
            "Bacteroides uniformis": "BU_ATCC8492",
            "Phocaeicola vulgatus": "PV_ATCC8482",
        }
