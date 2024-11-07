import ftplib
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from Bio import SeqIO
from django.core.management.base import BaseCommand
from django.db import transaction

from dataportal.models import Species, Strain, Contig


class Command(BaseCommand):
    help = "Imports strains and contigs from FTP and optionally sets type strains."

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
            default="./data-generators/data/gff-assembly-prefixes.tsv",
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
        prefix_mapping = dict(zip(prefix_df["assembly"], prefix_df["prefix"]))

        # Connect to FTP and import strains and contigs
        self.stdout.write("Starting strain and contig import...")
        self.import_strains_and_contigs(ftp_server, ftp_directory, prefix_mapping)

        # Set type strains if isolate names are provided
        if type_strain_isolates:
            self.set_type_strains(type_strain_isolates)

    def import_strains_and_contigs(self, ftp_server, ftp_directory, prefix_mapping):
        ftp = self.reconnect_ftp(ftp_server)
        ftp.cwd(ftp_directory)
        fasta_files = [f for f in ftp.nlst() if f.endswith(".fa")]
        self.stdout.write(f"Found {len(fasta_files)} FASTA files to process.")

        with ThreadPoolExecutor(
            max_workers=1
        ) as executor:  # Reduced to 1 to avoid overloading
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
            "Strain and contig data successfully imported into the database."
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

            # Determine species and create strain entry if needed
            species = Species.objects.filter(acronym=isolate_name.split("_")[0]).first()
            if not species:
                self.stdout.write(
                    f"No matching species found for isolate acronym {isolate_name.split('_')[0]}"
                )
                return

            self.stdout.write(f"Creating strain {isolate_name} ...")

            # Create strain
            with transaction.atomic():
                strain, created = Strain.objects.get_or_create(
                    isolate_name=isolate_name,
                    assembly_name=assembly_name,
                    assembly_accession=None,
                    fasta_file=file,
                    type_strain=False,
                    species=species,
                )

                # Retry download with reconnection if necessary
                local_file_path = f"/tmp/{file}"
                success = self.download_with_retry(ftp, file, local_file_path)
                if not success:
                    self.stdout.write(
                        f"Failed to download {file} after multiple attempts."
                    )
                    return

                # Bulk insert contigs
                contigs = []
                with open(local_file_path, "r") as fasta_local_file:
                    for record in SeqIO.parse(fasta_local_file, "fasta"):
                        contigs.append(
                            Contig(
                                strain=strain, seq_id=record.id, length=len(record.seq)
                            )
                        )
                Contig.objects.bulk_create(contigs, batch_size=1000)
                self.stdout.write(
                    f"Inserted {len(contigs)} contigs for strain {isolate_name}"
                )

                # Clean up local file
                os.remove(local_file_path)

            self.stdout.write(
                f"Successfully processed strain: {isolate_name} with assembly: {assembly_name}"
            )

        except Exception as e:
            self.stdout.write(f"Error processing {file}: {e}")

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
        self.stdout.write("Setting type strains for specified isolates.")
        updated_count = Strain.objects.filter(isolate_name__in=isolate_names).update(
            type_strain=True
        )
        self.stdout.write(f"Successfully updated {updated_count} type strains.")
