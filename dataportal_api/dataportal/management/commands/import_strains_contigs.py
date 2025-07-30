import ftplib
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from Bio import SeqIO
from django.core.management.base import BaseCommand

from dataportal.models import StrainDocument

# Note: Elasticsearch connection is already established in settings.py via elasticsearch_client.py
# This command uses the existing connection

SPECIES_ACRONYM_MAPPING = {"Bacteroides uniformis": "BU", "Phocaeicola vulgatus": "PV"}


class Command(BaseCommand):
    help = "Imports strains and contigs from FTP and indexes them into Elasticsearch."

    def add_arguments(self, parser):
        parser.add_argument("--ftp-server", type=str, default="ftp.ebi.ac.uk")
        parser.add_argument(
            "--ftp-directory",
            type=str,
            default="/pub/databases/mett/all_hd_isolates/deduplicated_assemblies/",
        )
        parser.add_argument(
            "--csv",
            type=str,
            default="../data-generators/data/gff-assembly-prefixes.tsv",
        )
        parser.add_argument(
            "--set-type-strains",
            nargs="+",
            help="List of isolate names to set as type strains (e.g., 'BU_ATCC8492 PV_ATCC8482')",
        )

    def handle(self, *args, **options):
        ftp_server = options["ftp_server"]
        ftp_directory = options["ftp_directory"]
        csv_path = options["csv"]
        type_strain_isolates = options["set_type_strains"]

        # Load the CSV mapping file
        prefix_df = pd.read_csv(csv_path, sep="\t")
        prefix_mapping = dict(
            zip(prefix_df["assembly"], prefix_df["prefix"], strict=False)
        )

        # Initialize assembly accession counter
        self.assembly_accession_counter = 1

        # Connect to FTP and import strains and contigs
        self.stdout.write("Starting strain and contig import...")
        self.import_strains_and_contigs(ftp_server, ftp_directory, prefix_mapping)

        # Update type strain field in Elasticsearch
        if type_strain_isolates:
            self.set_type_strains(type_strain_isolates)

    def import_strains_and_contigs(self, ftp_server, ftp_directory, prefix_mapping):
        ftp = self.reconnect_ftp(ftp_server)
        ftp.cwd(ftp_directory)
        fasta_files = [f for f in ftp.nlst() if f.endswith(".fa")]
        self.stdout.write(f"Found {len(fasta_files)} FASTA files to process.")

        with ThreadPoolExecutor(max_workers=1) as executor:  # Avoid overload
            futures = [
                executor.submit(
                    self.download_and_process_file, ftp, file, prefix_mapping
                )
                for file in fasta_files
            ]

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.stdout.write(f"Error processing file: {e}")

        ftp.quit()
        self.stdout.write(
            self.style.SUCCESS(
                "Strain and contig data successfully indexed into Elasticsearch."
            )
        )

    def download_and_process_file(self, ftp, file, prefix_mapping):
        try:
            assembly_name = os.path.splitext(file)[0]
            isolate_name = prefix_mapping.get(file)

            if not isolate_name:
                self.stdout.write(
                    f"No matching isolate found for assembly {assembly_name}"
                )
                return

            # Determine species name
            species_acronym, species_name = self.get_species_info(isolate_name)
            if not species_name:
                self.stdout.write(
                    f"No matching species found for isolate {isolate_name}"
                )
                return

            self.stdout.write(f"Processing strain {isolate_name} ...")

            # Generate Assembly Accession
            assembly_accession = f"AA{self.assembly_accession_counter:05d}"
            self.assembly_accession_counter += 1  # Increment for next strain

            # Retry download with reconnection if necessary
            local_file_path = f"/tmp/{file}"
            success = self.download_with_retry(ftp, file, local_file_path)
            if not success:
                self.stdout.write(f"Failed to download {file} after multiple attempts.")
                return

            # Extract contigs
            contigs = []
            with open(local_file_path) as fasta_local_file:
                for record in SeqIO.parse(fasta_local_file, "fasta"):
                    contigs.append({"seq_id": record.id, "length": len(record.seq)})

            # Create strain document
            strain_doc = StrainDocument(
                meta={"id": isolate_name},
                isolate_name=isolate_name,
                assembly_name=assembly_name,
                assembly_accession=assembly_accession,
                fasta_file=file,
                gff_file=None,
                type_strain=False,
                species_scientific_name=species_name,
                species_acronym=species_acronym,
                contigs=contigs,
            )

            # Save strain document to Elasticsearch
            strain_doc.save()
            self.stdout.write(
                f"Indexed strain {isolate_name} with {len(contigs)} contigs and accession {assembly_accession}."
            )

            # Clean up local file
            os.remove(local_file_path)

        except Exception as e:
            self.stdout.write(f"Error processing {file}: {e}")

    def get_species_info(self, isolate_name):
        """Extract species acronym and species name from isolate name."""
        species_acronym = isolate_name.split("_")[0] if "_" in isolate_name else None
        species_mapping = {
            "BU": "Bacteroides uniformis",
            "PV": "Phocaeicola vulgatus",
            # Add more mappings as needed
        }

        species_name = species_mapping.get(species_acronym, None)

        return species_acronym, species_name

    def download_with_retry(self, ftp, file, local_file_path, retries=3, delay=5):
        for attempt in range(retries):
            try:
                if attempt > 0:
                    self.stdout.write(
                        f"Reconnecting and retrying download for {file} (Attempt {attempt + 1})..."
                    )
                    ftp = self.reconnect_ftp(ftp.host)

                ftp.voidcmd("TYPE I")
                with open(local_file_path, "wb") as f:
                    ftp.retrbinary(f"RETR {file}", f.write)
                self.stdout.write(f"Downloaded {file} successfully.")
                return True
            except (ftplib.error_temp, ftplib.error_perm, ftplib.all_errors) as e:
                self.stdout.write(f"Attempt {attempt + 1} failed for {file}: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    self.stdout.write(
                        f"Download failed after {retries} attempts for {file}."
                    )
                    return False

    def reconnect_ftp(self, ftp_server):
        retries = 3
        for attempt in range(retries):
            try:
                ftp = ftplib.FTP(ftp_server)
                ftp.login()
                self.stdout.write(f"Connected to FTP server: {ftp_server}")
                return ftp
            except ftplib.all_errors as e:
                self.stdout.write(f"Connection failed on attempt {attempt + 1}: {e}")
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    self.stdout.write(f"Failed to reconnect after {retries} attempts.")
                    raise

    def set_type_strains(self, isolate_names):
        """Updates existing strains in Elasticsearch to set them as type strains"""
        self.stdout.write("Setting type strains for specified isolates.")

        for isolate_name in isolate_names:
            strain = StrainDocument.get(id=isolate_name, ignore=404)
            if strain:
                strain.type_strain = True
                strain.save()
                self.stdout.write(f"Updated strain {isolate_name} to type_strain=True")

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated {len(isolate_names)} type strains in Elasticsearch."
            )
        )
