import ftplib
import json
import logging
import os
import csv
from concurrent.futures import ThreadPoolExecutor
import time
import psycopg
from django.core.management.base import BaseCommand

logging.basicConfig(
    filename="process_gff.log",
    level=logging.DEBUG,  # Set to DEBUG for detailed information
    format="%(asctime)s %(levelname)s:%(message)s",
)

# Database query templates
gene_insert_query = """
INSERT INTO Gene (strain_id, gene_name, locus_tag, description, seq_id, cog, kegg, pfam, interpro, dbxref, 
ec_number, product, start_position, end_position, annotations)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
ON CONFLICT (locus_tag) DO NOTHING;
"""

ontology_insert_query = """
INSERT INTO Gene_Ontology_Term (gene_id, ontology_type, ontology_id, ontology_description)
VALUES (%s, %s, %s, %s)
ON CONFLICT DO NOTHING;
"""

update_strain_query = """
UPDATE Strain
SET gff_file = %s
WHERE isolate_name = %s
"""

# batch size for inserts
BATCH_SIZE = 1000


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
            "--mapping-task-file",
            type=str,
            default="./data-generators/data/gff-assembly-prefixes.tsv",
        )
        parser.add_argument(
            "--isolate", type=str, help="Specific isolate to import", required=False
        )
        parser.add_argument(
            "--assembly", type=str, help="Specific assembly to import", required=False
        )

    def handle(self, *args, **options):
        ftp_server = options["ftp_server"]
        ftp_directory = options["ftp_directory"]
        mapping_task_file = options["mapping_task_file"]
        target_isolate = options.get("isolate")
        target_assembly = options.get("assembly")

        logging.debug("Starting import process.")

        try:
            # Load the mapping task file
            logging.debug("Loading mapping task file...")
            isolate_to_assembly_map = {}
            with open(mapping_task_file, mode="r") as file:
                reader = csv.DictReader(file, delimiter="\t")
                for row in reader:
                    assembly_name = row["assembly"].replace(".fa", "")
                    isolate_to_assembly_map[row["prefix"]] = assembly_name
            logging.debug(
                f"Loaded mapping for {len(isolate_to_assembly_map)} isolates."
            )

            # Check if specific isolate or assembly is requested
            if target_isolate:
                isolates = [target_isolate]
            elif target_assembly:
                isolates = [
                    iso
                    for iso, asm in isolate_to_assembly_map.items()
                    if asm == target_assembly
                ]
                if not isolates:
                    logging.warning(
                        f"No isolates found for assembly: {target_assembly}"
                    )
                    return
            else:
                ftp = self.reconnect_ftp(ftp_server)
                ftp.cwd(ftp_directory)
                isolates = ftp.nlst()
                ftp.quit()

            logging.info(f"Found {len(isolates)} isolates to process.")

            # Process each isolate
            with ThreadPoolExecutor(max_workers=2) as executor:
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
        except Exception as e:
            logging.error(f"Error in the import process: {e}", exc_info=True)

    def reconnect_ftp(self, ftp_server):
        retries = 3
        for attempt in range(retries):
            try:
                logging.debug(
                    f"Connecting to FTP server {ftp_server} (attempt {attempt + 1})..."
                )
                ftp = ftplib.FTP(ftp_server)
                ftp.login()
                logging.info(f"Connected to FTP server: {ftp_server}")
                return ftp
            except ftplib.all_errors as e:
                logging.warning(f"Connection failed on attempt {attempt + 1}: {e}")
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    logging.error(f"Failed to reconnect after {retries} attempts.")
                    raise

    def list_files(self, ftp, path):
        logging.debug(f"Listing files in FTP path: {path}")
        try:
            file_list = ftp.nlst(path)
            logging.info(f"Files listed in {path}: {file_list}")
            return file_list
        except ftplib.error_perm as resp:
            if "No files found" in str(resp):
                logging.warning(f"No files found in {path}")
                return []
            else:
                logging.error(f"FTP error listing files in {path}: {resp}")
                raise

    def process_gff_file(self, gff_file, isolate, strain_id, ftp_server):
        logging.info(f"Starting processing of {gff_file} for isolate {isolate}")
        try:
            ftp = self.reconnect_ftp(ftp_server)
            local_gff_path = os.path.join("/tmp", os.path.basename(gff_file))
            with open(local_gff_path, "wb") as f:
                ftp.retrbinary(f"RETR {gff_file}", f.write)
            ftp.quit()
            logging.info(f"Downloaded {gff_file} to {local_gff_path}")

            genes_to_insert = []
            ontology_terms = []

            with open(local_gff_path, "r") as gff:
                line_count = 0
                for line in gff:
                    line_count += 1
                    if line.startswith("##FASTA"):
                        logging.info(f"Ignoring assembly sequence in {gff_file}")
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
                        logging.warning(
                            f"Skipping gene without locus_tag in {gff_file}"
                        )
                        continue

                    annotations = json.dumps(
                        {
                            "seq_id": seq_id,
                            "start_position": start,
                            "end_position": end,
                            "strand": strand,
                            "attributes": attr_dict,
                        }
                    )

                    genes_to_insert.append(
                        (
                            strain_id,
                            gene_name,
                            locus_tag,
                            description,
                            seq_id,
                            attr_dict.get("cog"),
                            attr_dict.get("kegg"),
                            attr_dict.get("pfam"),
                            attr_dict.get("interpro"),
                            attr_dict.get("Dbxref"),
                            attr_dict.get("eC_number"),
                            attr_dict.get("product"),
                            start,
                            end,
                            annotations,
                        )
                    )

                    if "interpro" in attr_dict:
                        for ont_id in attr_dict["interpro"].split(","):
                            ontology_terms.append(
                                (locus_tag, "InterPro", ont_id.strip(), None)
                            )

            logging.info(
                f"Parsed {line_count} lines from {gff_file}. Found {len(genes_to_insert)} genes and {len(ontology_terms)} ontology terms."
            )

            os.remove(local_gff_path)
            logging.info(f"Removed local GFF file {local_gff_path}")

            # Perform bulk insertions using psycopg
            with psycopg.connect(
                dbname="mett-dataportal-db",
                user="mett_dataportal-usr",
                password="mettpgpass",
                host="hh-rke-wp-webadmin-52-master-1.caas.ebi.ac.uk",
                port="31508",
                options="-c statement_timeout=60000",
            ) as conn:
                with conn.cursor() as cursor:
                    for i in range(0, len(genes_to_insert), BATCH_SIZE):
                        batch = genes_to_insert[i : i + BATCH_SIZE]
                        logging.info(f"Inserting batch of {len(batch)} genes...")
                        cursor.executemany(gene_insert_query, batch)
                        conn.commit()
                        logging.info(f"Inserted {len(batch)} genes in this batch.")

                    # todo Insert ontology terms
                    # for locus_tag, ontology_type, ontology_id, _ in ontology_terms:
                    #     cursor.execute(
                    #         "SELECT id FROM Gene WHERE locus_tag = %s", (locus_tag,)
                    #     )
                    #     gene_id = cursor.fetchone()
                    #     if gene_id:
                    #         cursor.execute(
                    #             ontology_insert_query,
                    #             (gene_id[0], ontology_type, ontology_id, None),
                    #         )
                    # logging.info(
                    #     f"Inserted {len(ontology_terms)} ontology terms for {gff_file}"
                    # )

                    cursor.execute(
                        update_strain_query, (os.path.basename(gff_file), isolate)
                    )
                    logging.info(
                        f"Updated Strain table with GFF file {os.path.basename(gff_file)} for isolate: {isolate}"
                    )

                conn.commit()
                logging.info("Transaction committed.")

        except Exception as e:
            logging.error(f"Error processing GFF file {gff_file}: {e}", exc_info=True)

    def process_isolate(
        self, isolate, ftp_server, ftp_directory, isolate_to_assembly_map
    ):
        retries = 5
        for attempt in range(retries):
            try:
                logging.info(f"Processing isolate: {isolate} (Attempt {attempt + 1})")
                assembly_name = isolate_to_assembly_map.get(isolate)

                ftp = self.reconnect_ftp(ftp_server)
                isolate_path = (
                    f"{ftp_directory}/{isolate}/functional_annotation/merged_gff/"
                )
                gff_files_in_isolate = self.list_files(ftp, isolate_path)
                ftp.quit()

                if not gff_files_in_isolate:
                    logging.warning(f"No GFF files found for isolate {isolate}")
                    return

                with psycopg.connect(
                    dbname="mett-dataportal-db",
                    user="mett_dataportal-usr",
                    password="mettpgpass",
                    host="hh-rke-wp-webadmin-52-master-1.caas.ebi.ac.uk",
                    port="31508",
                    options="-c statement_timeout=60000",
                ) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "SELECT id FROM Strain WHERE assembly_name = %s",
                            (assembly_name,),
                        )
                        strain_id = cursor.fetchone()

                        if not strain_id:
                            logging.error(f"No strain_id found for isolate: {isolate}")
                            return

                logging.debug(f"Strain ID for {isolate} is {strain_id[0]}.")

                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [
                        executor.submit(
                            self.process_gff_file,
                            gff_file,
                            isolate,
                            strain_id[0],
                            ftp_server,
                        )
                        for gff_file in gff_files_in_isolate
                        if gff_file.endswith("_annotations.gff")
                    ]

                    for future in futures:
                        future.result()

                logging.info(f"Successfully processed isolate: {isolate}")
                break

            except Exception as e:
                logging.error(
                    f"Error processing isolate {isolate} on attempt {attempt + 1}: {e}",
                    exc_info=True,
                )
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    logging.error(
                        f"Failed to process isolate {isolate} after {retries} attempts."
                    )
