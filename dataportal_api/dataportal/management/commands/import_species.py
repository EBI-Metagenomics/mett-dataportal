import ftplib
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from Bio import SeqIO
from django.core.management.base import BaseCommand
from elasticsearch import Elasticsearch, helpers

# Load Elasticsearch environment variables
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_USER = os.getenv("ES_USER")
ES_PASSWORD = os.getenv("ES_PASSWORD")

# Elasticsearch connection
if ES_USER and ES_PASSWORD:
    es = Elasticsearch(ES_HOST, basic_auth=(ES_USER, ES_PASSWORD))
else:
    es = Elasticsearch(ES_HOST)

INDEX_NAME = "strain_index"  # Strain index in Elasticsearch


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
        prefix_mapping = dict(zip(prefix_df["assembly"], prefix_df["prefix"]))

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
                executor.submit(self.download_and_process_file, ftp, file, prefix_mapping)
                for file in fasta_files
            ]

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.stdout.write(f"Error processing file: {e}")

        ftp.quit()
        self.stdout.write(self.style.SUCCESS("Strain and contig data successfully indexed into Elasticsearch."))

    def download_and_process_file(self, ftp, file, prefix_mapping):
        try:
            assembly_name = os.path.splitext(file)[0]
            isolate_name = prefix_mapping.get(file)

            if not isolate_name:
                self.stdout.write(f"No matching isolate found for assembly {assembly_name}")
                return

            # Create strain document
            strain_doc = {
                "_index": INDEX_NAME,
                "_id": isolate_name,  # Use isolate_name as ID to avoid duplicates
                "_source": {
                    "isolate_name": isolate_name,
                    "assembly_name": assembly_name,
                    "assembly_accession": None,
                    "fasta_file": file,
                    "type_strain": False,
                    "contigs": [],  # Contigs will be added here
                },
            }

            # Retry download with reconnection if necessary
            local_file_path = f"/tmp/{file}"
            success = self.download_with_retry(ftp, file, local_file_path)
            if not success:
                self.stdout.write(f"Failed to download {file} after multiple attempts.")
                return

            # Extract contigs and store in the strain document
            with open(local_file_path, "r") as fasta_local_file:
                for record in SeqIO.parse(fasta_local_file, "fasta"):
                    strain_doc["_source"]["contigs"].append(
                        {"seq_id": record.id, "length": len(record.seq)}
                    )

            # Index the strain document into Elasticsearch
            es.index(index=INDEX_NAME, id=strain_doc["_id"], body=strain_doc["_source"])
            self.stdout.write(f"Indexed strain {isolate_name} with {len(strain_doc['_source']['contigs'])} contigs.")

            # Clean up local file
            os.remove(local_file_path)

        except Exception as e:
            self.stdout.write(f"Error processing {file}: {e}")

    def download_with_retry(self, ftp, file, local_file_path, retries=3, delay=5):
        for attempt in range(retries):
            try:
                if attempt > 0:
                    self.stdout.write(f"Reconnecting and retrying download for {file} (Attempt {attempt + 1})...")
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
                    self.stdout.write(f"Download failed after {retries} attempts for {file}.")
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
        """ Updates existing strains in Elasticsearch to set them as type strains """
        self.stdout.write("Setting type strains for specified isolates.")

        for isolate_name in isolate_names:
            script = {
                "script": {
                    "source": "ctx._source.type_strain = true",
                    "lang": "painless",
                }
            }
            es.update(index=INDEX_NAME, id=isolate_name, body=script)

        self.stdout.write(self.style.SUCCESS(f"Updated {len(isolate_names)} type strains in Elasticsearch."))
