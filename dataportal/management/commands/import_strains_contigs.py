import ftplib
import os
from datetime import time

import pandas as pd
from Bio import SeqIO
from django.core.management.base import BaseCommand
from dataportal.models import Species, Strain, Contig  # Import your models


class Command(BaseCommand):
    help = "Imports strains and contigs from FTP and optionally sets type strains."

    def add_arguments(self, parser):
        parser.add_argument("--ftp-server", type=str, default="ftp.ebi.ac.uk")
        parser.add_argument(
            "--ftp-directory",
            type=str,
            default="/pub/databases/mett/all_hd_isolates/deduplicated_assemblies/",
        )
        parser.add_argument("--csv", type=str, default="gff-assembly-prefixes.tsv")
        parser.add_argument("--assembly-start", type=int, default=123456)
        parser.add_argument(
            "--set-type-strains",
            nargs="+",
            help="List of isolate names to set as type strains (e.g., 'BU_ATCC8492 PV_ATCC8482')",
        )

    def handle(self, *args, **options):
        ftp_server = options["ftp_server"]
        ftp_directory = options["ftp_directory"]
        csv_path = options["csv"]
        assembly_accession_start = options["assembly_start"]
        type_strain_isolates = options["set_type_strains"]

        # Load the CSV mapping file
        prefix_df = pd.read_csv(csv_path, sep="\t")
        prefix_mapping = dict(zip(prefix_df["assembly"], prefix_df["prefix"]))

        # Connect to FTP and import strains and contigs
        self.import_strains_and_contigs(
            ftp_server, ftp_directory, prefix_mapping, assembly_accession_start
        )

        # Set type strains if isolate names are provided
        if type_strain_isolates:
            self.set_type_strains(type_strain_isolates)

    def import_strains_and_contigs(
        self, ftp_server, ftp_directory, prefix_mapping, assembly_accession_start
    ):
        ftp = self.reconnect_ftp(ftp_server)
        ftp.cwd(ftp_directory)
        fasta_files = [f for f in ftp.nlst() if f.endswith(".fa")]

        current_accession_number = assembly_accession_start

        for file in fasta_files:
            assembly_name = os.path.splitext(file)[0]
            isolate_name = prefix_mapping.get(file)

            if isolate_name:
                assembly_accession = str(current_accession_number)
                species = Species.objects.filter(
                    acronym=isolate_name.split("_")[0]
                ).first()

                if species:
                    # Create a new strain entry if it doesn't exist
                    strain, created = Strain.objects.get_or_create(
                        isolate_name=isolate_name,
                        assembly_name=assembly_name,
                        assembly_accession=assembly_accession,
                        fasta_file=file,
                        type_strain=False,
                        species=species,
                    )

                    # Download the FASTA file
                    with open(f"/tmp/{file}", "wb") as fasta_local_file:
                        ftp.retrbinary(f"RETR {file}", fasta_local_file.write)

                    # Insert contig records
                    with open(f"/tmp/{file}", "r") as fasta_local_file:
                        for record in SeqIO.parse(fasta_local_file, "fasta"):
                            Contig.objects.get_or_create(
                                strain=strain, seq_id=record.id, length=len(record.seq)
                            )
                            self.stdout.write(
                                f"Inserted contig {record.id} for strain {isolate_name}"
                            )

                    # Clean up local file
                    os.remove(f"/tmp/{file}")

                    self.stdout.write(
                        f"Processed strain: {isolate_name} with assembly: {assembly_name}"
                    )
                    current_accession_number += 1
                else:
                    self.stdout.write(
                        f"No matching species found for isolate acronym {isolate_name.split('_')[0]}"
                    )
            else:
                self.stdout.write(
                    f"No matching isolate found for assembly {assembly_name}"
                )

        ftp.quit()
        self.stdout.write(
            "Strain and contig data successfully imported into the database."
        )

    def reconnect_ftp(self, ftp_server):
        retries = 3
        for attempt in range(retries):
            try:
                ftp = ftplib.FTP(ftp_server)
                ftp.login()
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
