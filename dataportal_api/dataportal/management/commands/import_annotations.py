import os
import csv
import ftplib
import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from Bio import SeqIO
import pandas as pd
from django.core.management.base import BaseCommand
from elasticsearch_dsl import connections
from elasticsearch.helpers import bulk
from dataportal.elasticsearch.models import GeneDocument

# Load environment variables for Elasticsearch
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_USER = os.getenv("ES_USER")
ES_PASSWORD = os.getenv("ES_PASSWORD")

# Establish Elasticsearch connection
connections.create_connection(hosts=[ES_HOST], http_auth=(ES_USER, ES_PASSWORD))

# Logging configuration
logging.basicConfig(
    filename="import_genes.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
)

BATCH_SIZE = 500


class Command(BaseCommand):
    help = "Imports gene annotations and essentiality data into Elasticsearch."

    def add_arguments(self, parser):
        parser.add_argument("--ftp-server", type=str, default="ftp.ebi.ac.uk")
        parser.add_argument(
            "--ftp-directory",
            type=str,
            default="/pub/databases/mett/annotations/v1_2024-04-15/",
        )
        parser.add_argument(
            "--mapping-task-file",
            type=str,
            default="../data-generators/data/gff-assembly-prefixes.tsv",
        )
        parser.add_argument(
            "--essentiality-csv",
            type=str,
            default="../data-generators/data/essentiality_table_all_libraries.csv",
        )

    def handle(self, *args, **options):
        ftp_server = options["ftp_server"]
        ftp_directory = options["ftp_directory"]
        mapping_task_file = options["mapping_task_file"]
        essentiality_csv = options["essentiality_csv"]

        logging.info("Starting gene import process.")

        try:
            # Load isolate-to-assembly mapping
            isolate_to_assembly_map = self.load_isolate_mapping(mapping_task_file)

            # Fetch list of isolates from FTP
            ftp = self.reconnect_ftp(ftp_server)
            ftp.cwd(ftp_directory)
            isolates = ftp.nlst()
            ftp.quit()

            logging.info(f"Found {len(isolates)} isolates to process.")

            # Process each isolate in parallel
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(
                        self.process_isolate, isolate, ftp_server, ftp_directory, isolate_to_assembly_map
                    )
                    for isolate in isolates
                ]
                for future in futures:
                    future.result()

            logging.info("GFF files processed successfully.")

            # Import essentiality data and update gene index
            self.import_essentiality_data(essentiality_csv)

            logging.info("Gene annotations and essentiality data imported successfully.")

        except Exception as e:
            logging.error(f"Error in the import process: {e}", exc_info=True)

    def load_isolate_mapping(self, mapping_task_file):
        """ Load isolate-to-assembly mapping from TSV file. """
        mapping = {}
        with open(mapping_task_file, mode="r") as file:
            reader = csv.DictReader(file, delimiter="\t")
            for row in reader:
                assembly_name = row["assembly"].replace(".fa", "")
                mapping[row["prefix"]] = assembly_name
        return mapping

    def reconnect_ftp(self, ftp_server):
        """ Handle FTP connection with retry logic. """
        retries = 3
        for attempt in range(retries):
            try:
                ftp = ftplib.FTP(ftp_server)
                ftp.login()
                return ftp
            except ftplib.all_errors as e:
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    raise

    def process_isolate(self, isolate, ftp_server, ftp_directory, isolate_to_assembly_map):
        """ Process GFF files for a given isolate. """
        try:
            assembly_name = isolate_to_assembly_map.get(isolate)

            ftp = self.reconnect_ftp(ftp_server)
            isolate_path = f"{ftp_directory}/{isolate}/functional_annotation/merged_gff/"
            gff_files = ftp.nlst(isolate_path)
            ftp.quit()

            if not gff_files:
                return

            for gff_file in gff_files:
                if gff_file.endswith("_annotations.gff"):
                    self.process_gff_file(gff_file, isolate, ftp_server)

        except Exception as e:
            logging.error(f"Error processing isolate {isolate}: {e}", exc_info=True)

    def process_gff_file(self, gff_file, isolate, ftp_server):
        """ Process GFF file and index gene data into Elasticsearch. """
        try:
            ftp = self.reconnect_ftp(ftp_server)
            local_gff_path = os.path.join("/tmp", os.path.basename(gff_file))
            with open(local_gff_path, "wb") as f:
                ftp.retrbinary(f"RETR {gff_file}", f.write)
            ftp.quit()

            genes_to_index = []

            with open(local_gff_path, "r") as gff:
                for line in gff:
                    if line.startswith("#"):
                        continue

                    columns = line.strip().split("\t")
                    if len(columns) != 9 or columns[2] != "gene":
                        continue

                    seq_id, _, _, start, end, _, strand, _, attributes = columns
                    attr_dict = dict(
                        item.split("=") for item in attributes.split(";") if "=" in item
                    )

                    gene_name = attr_dict.get("Name")
                    locus_tag = attr_dict.get("locus_tag")
                    product = attr_dict.get("product")
                    annotations = json.dumps(attr_dict)

                    if not locus_tag:
                        continue

                    genes_to_index.append(
                        GeneDocument(
                            meta={"id": locus_tag},
                            gene_name=gene_name,
                            locus_tag=locus_tag,
                            product=product,
                            seq_id=seq_id,
                            start=int(start),
                            end=int(end),
                            annotations=annotations,
                        )
                    )

                    if len(genes_to_index) >= BATCH_SIZE:
                        bulk(connections.get_connection(), (doc.to_dict(include_meta=True) for doc in genes_to_index))
                        genes_to_index.clear()

            if genes_to_index:
                bulk(connections.get_connection(), (doc.to_dict(include_meta=True) for doc in genes_to_index))

            os.remove(local_gff_path)

        except Exception as e:
            logging.error(f"Error processing GFF file {gff_file}: {e}", exc_info=True)

    def import_essentiality_data(self, essentiality_csv):
        """ Import essentiality data and update genes in Elasticsearch. """
        try:
            essentiality_data = pd.read_csv(essentiality_csv)

            valid_strains = ["BU_ATCC8492", "PV_ATCC8482"]
            valid_essentiality_categories = {
                "essential": "Essential",
                "essential_liquid": "Essential Liquid",
                "essential_solid": "Essential Solid",
                "not_essential": "Not Essential",
                "unclear": "Unclear",
            }

            updates = []
            for row in essentiality_data.itertuples():
                locus_tag = row.locus_tag.strip()
                strain_id = "_".join(locus_tag.split("_")[:2])
                essentiality_value = row.unified_final_call_240817.strip().lower()

                if strain_id in valid_strains and essentiality_value in valid_essentiality_categories:
                    updates.append({
                        "_op_type": "update",
                        "_index": "gene_index",
                        "_id": locus_tag,
                        "doc": {"essentiality": valid_essentiality_categories[essentiality_value]},
                    })

                    if len(updates) >= BATCH_SIZE:
                        bulk(connections.get_connection(), updates)
                        updates.clear()

            if updates:
                bulk(connections.get_connection(), updates)

            logging.info("Essentiality data successfully updated in Elasticsearch.")

        except Exception as e:
            logging.error(f"Error importing essentiality data: {e}", exc_info=True)
