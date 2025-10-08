#!/usr/bin/env python3
"""
Example script demonstrating how to use the updated PPI import with gene information.

This script shows how to:
1. Initialize the GFF parser
2. Create a PPI CSV flow with gene information
3. Run the import process
"""

import os
import sys
from pathlib import Path

# Add the dataportal_api directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from dataportal.ingest.ppi.gff_parser import GFFParser
from dataportal.ingest.ppi.flows.ppi_csv import PPICSVFlow
from dataportal.ingest.es_repo import PPIIndexRepository


def main():
    """Example usage of PPI import with gene information."""
    
    # Initialize the GFF parser
    print("Initializing GFF parser...")
    gff_parser = GFFParser(
        ftp_server="ftp.ebi.ac.uk",  # You can change this to a different FTP server
        ftp_directory="/pub/databases/mett/annotations/v1_2024-04-15/"  # You can change this path
    )
    print(f"FTP Server: {gff_parser.ftp_server}")
    print(f"FTP Directory: {gff_parser.ftp_directory}")
    
    # Initialize the PPI repository
    print("Initializing PPI repository...")
    repo = PPIIndexRepository(concrete_index="ppi_index")
    
    # Species mapping (you may need to adjust this based on your data)
    species_map = {
        "Bacteroides uniformis": "BU_ATCC8492",
        "Phocaeicola vulgatus": "PV_ATCC8482",
    }
    
    # Create the PPI CSV flow with gene information
    print("Creating PPI CSV flow...")
    flow = PPICSVFlow(
        repo=repo,
        species_map=species_map,
        gff_parser=gff_parser  # This enables gene information extraction
    )
    
    # Example: Run the import process
    # Replace with your actual CSV folder path
    csv_folder = "/path/to/your/ppi/csv/files"
    
    if not os.path.exists(csv_folder):
        print(f"CSV folder not found: {csv_folder}")
        print("Please update the csv_folder variable with the correct path to your PPI CSV files.")
        return
    
    print(f"Running PPI import with gene information from: {csv_folder}")
    
    try:
        # Run the import process
        total_indexed = flow.run(
            folder=csv_folder,
            pattern="*.csv",
            batch_size=5000,  # Adjust based on your system's memory
            refresh="wait_for",  # Wait for indexing to complete
            log_every=10000,  # Log progress every 10000 records
            optimize_indexing=True,
            refresh_every_rows=50000,  # Refresh every 50000 rows (optional)
            refresh_every_secs=300.0   # Refresh every 5 minutes (optional)
        )
        
        print(f"Successfully indexed {total_indexed} PPI records with gene information!")
        
    except Exception as e:
        print(f"Error during import: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clear the GFF parser cache to free memory
        gff_parser.clear_cache()
        print("GFF parser cache cleared.")


if __name__ == "__main__":
    main()
