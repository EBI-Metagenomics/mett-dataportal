"""
Management command to import ortholog data with gene information from GFF files.

This command extends the existing ortholog import functionality to include gene information
extracted from GFF files, with in-memory caching to avoid re-downloading the same files.
"""

import os
import logging
import ftplib
import re
from django.core.management.base import BaseCommand, CommandError
from dataportal.ingest.ppi.gff_parser import GFFParser
from dataportal.ingest.ortholog.flows.orthologs import Orthologs

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import ortholog data with gene information from GFF files"

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--ortholog-file",
            type=str,
            help="Path to ortholog TSV file"
        )
        group.add_argument(
            "--ortholog-directory",
            type=str,
            help="Path to directory containing ortholog TSV files"
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
            "--chunksize",
            type=int,
            default=100_000,
            help="Chunk size for processing (default: 100000)"
        )
        parser.add_argument(
            "--flush-every",
            type=int,
            default=200_000,
            help="Flush to index every N records (default: 200000)"
        )
        parser.add_argument(
            "--no-gene-info",
            action="store_true",
            help="Skip gene information extraction (faster but no gene data)"
        )
        parser.add_argument(
            "--index",
            type=str,
            help="Elasticsearch index name (optional, uses default if not specified)"
        )
        parser.add_argument(
            "--max-gff-files",
            type=int,
            default=50,
            help="Maximum number of GFF files to load at once (default: 50, set to 0 for all)"
        )

    def _get_available_isolates_from_ftp(self, ftp_server: str, ftp_directory: str) -> set:
        """Get list of available isolates from FTP server directory listing."""
        isolates = set()
        
        try:
            # Connect to FTP server
            ftp = ftplib.FTP(ftp_server)
            ftp.login()
            
            # Change to the annotations directory
            ftp.cwd(ftp_directory)
            
            # Get directory listing
            file_list = []
            ftp.retrlines('LIST', file_list.append)
            
            # Parse directory listing to extract isolate names
            # Look for directories that match the pattern BU_* or PV_*
            isolate_pattern = re.compile(r'^d.*\s+(BU_[^/\s]+|PV_[^/\s]+)/?\s*$')
            
            for line in file_list:
                match = isolate_pattern.match(line)
                if match:
                    isolate_name = match.group(1)
                    isolates.add(isolate_name)
            
            ftp.quit()
            
            self.stdout.write(f"Found {len(isolates)} isolates on FTP server: {sorted(isolates)}")
            
        except Exception as e:
            self.stdout.write(f"Error accessing FTP server {ftp_server}: {e}")
            raise
        
        return isolates

    def handle(self, *args, **options):
        ortholog_file = options.get("ortholog_file")
        ortholog_directory = options.get("ortholog_directory")
        ftp_server = options["ftp_server"]
        ftp_directory = options["ftp_directory"]
        chunksize = options["chunksize"]
        flush_every = options["flush_every"]
        no_gene_info = options["no_gene_info"]
        index_name = options.get("index")
        max_gff_files = options["max_gff_files"]

        # Determine files to process
        files_to_process = []
        
        if ortholog_file:
            if not os.path.exists(ortholog_file):
                raise CommandError(f"Ortholog file not found: {ortholog_file}")
            files_to_process = [ortholog_file]
        elif ortholog_directory:
            if not os.path.exists(ortholog_directory):
                raise CommandError(f"Ortholog directory not found: {ortholog_directory}")
            
            # Find all .txt files in the directory
            import glob
            pattern = os.path.join(ortholog_directory, "*.txt")
            files_to_process = glob.glob(pattern)
            
            if not files_to_process:
                raise CommandError(f"No .txt files found in directory: {ortholog_directory}")
            
            self.stdout.write(f"Found {len(files_to_process)} ortholog files to process")

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

        # Pre-load all GFF files if gene information is requested
        if gff_parser and not no_gene_info:
            self.stdout.write("Pre-loading GFF files for all species...")
            
            # Get available isolates directly from FTP directory listing
            try:
                available_isolates = self._get_available_isolates_from_ftp(ftp_server, ftp_directory)
                self.stdout.write(f"Found {len(available_isolates)} available isolates from FTP server")
                
                if available_isolates:
                    # Limit the number of GFF files to load if specified
                    if max_gff_files > 0 and len(available_isolates) > max_gff_files:
                        self.stdout.write(f"Limiting to {max_gff_files} GFF files (use --max-gff-files 0 for all)")
                        # Prioritize common isolates first
                        priority_isolates = []
                        for isolate in sorted(available_isolates):
                            if any(common in isolate for common in ['ATCC', 'AN67', 'CL11T00C01', '61', '909']):
                                priority_isolates.append(isolate)
                        
                        # Add remaining isolates up to the limit
                        remaining_isolates = [iso for iso in sorted(available_isolates) if iso not in priority_isolates]
                        selected_isolates = priority_isolates + remaining_isolates[:max_gff_files - len(priority_isolates)]
                        available_isolates = set(selected_isolates)
                        self.stdout.write(f"Selected {len(available_isolates)} isolates for GFF loading")
                    
                    # Create species-isolate mapping for selected isolates
                    species_isolate_mapping = {}
                    for isolate in sorted(available_isolates):
                        # Extract species from isolate name (e.g., "BU_61" -> "Bacteroides uniformis")
                        species_acronym = isolate.split('_')[0]
                        species_map = {
                            "BU": "Bacteroides uniformis",
                            "PV": "Phocaeicola vulgatus",
                        }
                        species_name = species_map.get(species_acronym, f"Unknown {species_acronym}")
                        
                        # Create a unique species name for each isolate to force loading all GFF files
                        unique_species_name = f"{species_name}_{isolate}"
                        species_isolate_mapping[unique_species_name] = isolate
                    
                    self.stdout.write(f"Species-isolate mapping (with unique species names):")
                    for species, isolate in species_isolate_mapping.items():
                        self.stdout.write(f"  {species} -> {isolate}")
                    
                    # Set the mapping and preload GFF files with throttling
                    gff_parser.set_species_mapping(species_isolate_mapping)
                    species_list = list(species_isolate_mapping.keys())
                    gff_parser.preload_gff_files(species_list)
                    self.stdout.write(f"Pre-loaded GFF files for {len(species_list)} species")
                    
                    # Store all isolates for later use in gene lookup
                    gff_parser._all_isolates = available_isolates
                else:
                    self.stdout.write("No isolates found on FTP server, skipping GFF preload")
                    
            except Exception as e:
                self.stdout.write(f"Error getting isolates from FTP server: {e}")
                self.stdout.write("Falling back to scanning ortholog files...")
                
                # Fallback to the old method
                all_isolates = set()
                for file_path in files_to_process:
                    temp_flow = Orthologs(index_name="temp", gff_parser=None)
                    file_isolates = temp_flow._get_all_isolates_from_file(file_path)
                    all_isolates.update(file_isolates)
                
                if all_isolates:
                    self.stdout.write(f"Found {len(all_isolates)} unique isolates from files: {sorted(all_isolates)}")
                    # ... rest of the fallback logic would go here
                else:
                    self.stdout.write("No isolates found in any files, skipping GFF preload")

        # Initialize ortholog flow
        self.stdout.write("Initializing ortholog flow...")
        
        # Use custom index if specified, otherwise use default
        if not index_name:
            index_name = "ortholog_index"  # Default index name
        
        ortholog_flow = Orthologs(
            index_name=index_name,
            gff_parser=gff_parser
        )
        self.stdout.write(f"Using index: {index_name}")

        # Run the import process
        self.stdout.write(f"Starting ortholog import from {len(files_to_process)} file(s)")
        self.stdout.write(f"Chunk size: {chunksize}")
        self.stdout.write(f"Flush every: {flush_every}")
        self.stdout.write(f"Gene information: {'Enabled' if gff_parser else 'Disabled'}")
        if gff_parser:
            self.stdout.write(f"FTP Server: {ftp_server}")
            self.stdout.write(f"FTP Directory: {ftp_directory}")

        total_processed = 0
        successful_files = 0
        failed_files = 0

        try:
            for i, file_path in enumerate(files_to_process, 1):
                self.stdout.write(f"\nProcessing file {i}/{len(files_to_process)}: {os.path.basename(file_path)}")
                
                try:
                    # Reuse the same flow instance to benefit from GFF cache
                    ortholog_flow.run(
                        path=file_path,
                        chunksize=chunksize,
                        flush_every=flush_every
                    )
                    
                    successful_files += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Successfully processed: {os.path.basename(file_path)}")
                    )
                    
                except Exception as e:
                    failed_files += 1
                    self.stdout.write(
                        self.style.ERROR(f"✗ Failed to process {os.path.basename(file_path)}: {e}")
                    )
                    # Continue with other files instead of stopping
                    continue

            # Summary
            self.stdout.write(f"\n" + "="*50)
            self.stdout.write(f"Import Summary:")
            self.stdout.write(f"  Total files: {len(files_to_process)}")
            self.stdout.write(f"  Successful: {successful_files}")
            self.stdout.write(f"  Failed: {failed_files}")
            
            if successful_files > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully imported ortholog data from {successful_files} file(s)!"
                    )
                )
            
            if failed_files > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"Warning: {failed_files} file(s) failed to process"
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
