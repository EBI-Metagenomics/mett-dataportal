import csv
import ftplib
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor

from django.core.management.base import BaseCommand

from dataportal.models import Strain, Gene, GeneOntologyTerm

# Configure logging
logging.basicConfig(
    filename="process_gff.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
)


class Command(BaseCommand):
    help = "Imports gene annotations from GFF files via FTP and inserts them into the database."

    def add_arguments(self, parser):
        parser.add_argument("--ftp-server", type=str, default="ftp.ebi.ac.uk")
        parser.add_argument(
            "--ftp-directory",
            type=str,
            default="/pub/databases/mett/annotations/v1_2024-04-15/",
        )
        parser.add_argument(
            "--mapping-task-file", type=str, default="./gff-assembly-prefixes.tsv"
        )

    def handle(self, *args, **options):
        ftp_server = options["ftp_server"]
        ftp_directory = options["ftp_directory"]
        mapping_task_file = options["mapping_task_file"]

        # Load the mapping file into a dictionary
        isolate_to_assembly_map = {}
        with open(mapping_task_file, mode="r") as file:
            reader = csv.DictReader(file, delimiter="\t")
            for row in reader:
                assembly_name = row["assembly"].replace(".fa", "")
                isolate_to_assembly_map[row["prefix"]] = assembly_name

        # Process each isolate
        ftp = self.reconnect_ftp(ftp_server)
        ftp.cwd(ftp_directory)
        isolates = ftp.nlst()
        ftp.quit()

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(
                    self.process_isolate,
                    isolate,
                    ftp_server,
                    ftp_directory,
                    isolate_to_assembly_map,
                )
                for isolate in isolates
            ]
            for future in futures:
                future.result()

        logging.info("GFF files processed, and strain table updated.")

    def reconnect_ftp(self, ftp_server):
        retries = 3
        for attempt in range(retries):
            try:
                ftp = ftplib.FTP(ftp_server)
                ftp.login()
                return ftp
            except ftplib.all_errors as e:
                logging.warning(f"Connection failed on attempt {attempt + 1}: {e}")
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    logging.error(f"Failed to reconnect after {retries} attempts.")
                    raise

    def process_isolate(
        self, isolate, ftp_server, ftp_directory, isolate_to_assembly_map
    ):
        assembly_name = isolate_to_assembly_map.get(isolate)
        ftp = self.reconnect_ftp(ftp_server)
        isolate_path = f"{ftp_directory}/{isolate}/functional_annotation/merged_gff/"
        gff_files_in_isolate = self.list_files(ftp, isolate_path)
        ftp.quit()

        if not gff_files_in_isolate:
            logging.warning(f"No GFF files found for isolate {isolate}")
            return

        strain = Strain.objects.filter(assembly_name=assembly_name).first()
        if not strain:
            logging.error(f"No strain found for isolate: {isolate}")
            return

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(
                    self.process_gff_file, gff_file, isolate, strain.id, ftp_server
                )
                for gff_file in gff_files_in_isolate
                if gff_file.endswith("_annotations.gff")
            ]
            for future in futures:
                future.result()

        logging.info(f"Successfully processed isolate: {isolate}")

    def list_files(self, ftp, path):
        try:
            return ftp.nlst(path)
        except ftplib.error_perm as resp:
            if "No files found" in str(resp):
                logging.warning(f"No files found in {path}")
                return []
            else:
                logging.error(f"FTP error listing files in {path}: {resp}")
                raise

    def process_gff_file(self, gff_file, isolate, strain_id, ftp_server):
        logging.info(f"Starting processing of {gff_file} for isolate {isolate}")
        ftp = self.reconnect_ftp(ftp_server)
        local_gff_path = os.path.join("/tmp", os.path.basename(gff_file))
        with open(local_gff_path, "wb") as f:
            ftp.retrbinary(f"RETR {gff_file}", f.write)
        ftp.quit()

        with open(local_gff_path, "r") as gff:
            for line in gff:
                if line.startswith("##FASTA"):
                    break
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
                description = attr_dict.get("product")

                if not locus_tag:
                    continue

                gene, created = Gene.objects.get_or_create(
                    strain_id=strain_id,
                    gene_name=gene_name,
                    locus_tag=locus_tag,
                    defaults={
                        "description": description,
                        "seq_id": seq_id,
                        "cog": attr_dict.get("cog"),
                        "kegg": attr_dict.get("kegg"),
                        "pfam": attr_dict.get("pfam"),
                        "interpro": attr_dict.get("interpro"),
                        "dbxref": attr_dict.get("Dbxref"),
                        "ec_number": attr_dict.get("eC_number"),
                        "product": description,
                        "start_position": start,
                        "end_position": end,
                        "annotations": {
                            "seq_id": seq_id,
                            "start_position": start,
                            "end_position": end,
                            "strand": strand,
                            "attributes": attr_dict,
                        },
                    },
                )

                # Insert ontology terms if available
                if "interpro" in attr_dict:
                    for ont_id in attr_dict["interpro"].split(","):
                        GeneOntologyTerm.objects.get_or_create(
                            gene=gene,
                            ontology_type="InterPro",
                            ontology_id=ont_id.strip(),
                        )

        os.remove(local_gff_path)
        logging.info(f"Processed and removed local GFF file: {local_gff_path}")
