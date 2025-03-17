import os
import csv
import ftplib
import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from Bio import SeqIO
import pandas as pd
from django.core.management.base import BaseCommand
from elasticsearch_dsl import connections
from elasticsearch.helpers import bulk
from dataportal.elasticsearch.models import GeneDocument, StrainDocument

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

SPECIES_ACRONYM_MAPPING = {
    "Bacteroides uniformis": "BU",
    "Phocaeicola vulgatus": "PV"
}

BATCH_SIZE = 500  # Bulk size for indexing


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
            default="../data-generators/data/essentiality_table_all_libraries_240818_14102024.csv",
        )
        parser.add_argument(
            "--expected-records", type=int, default=449621, help="Expected number of total records in gene_index"
        )
        parser.add_argument(
            "--isolate", type=str, help="Specific isolate to process"
        )
        parser.add_argument(
            "--assembly", type=str, help="Specific assembly to process"
        )

    def get_species_acronym(self, species_scientific_name):
        """ Returns species acronym based on static mapping. """
        return SPECIES_ACRONYM_MAPPING.get(species_scientific_name, None)

    def parse_dbxref(self, dbxref_string):
        """ Convert dbxref string into a structured format and extract IDs. """
        dbxref_list = dbxref_string.split(",") if dbxref_string else []
        parsed_dbxref = []
        uniprot_id, cog_id = None, None

        for entry in dbxref_list:
            if ":" in entry:
                db, ref = entry.split(":", 1)
                parsed_dbxref.append({"db": db, "ref": ref})

                # Extract specific fields
                if db == "UniProt":
                    uniprot_id = ref
                elif db == "COG":
                    cog_id = ref

        return parsed_dbxref, uniprot_id or None, cog_id or None  # Ensure three values are returned

    def handle(self, *args, **options):
        ftp_server = options["ftp_server"]
        ftp_directory = options["ftp_directory"]
        mapping_task_file = options["mapping_task_file"]
        essentiality_csv = options["essentiality_csv"]
        expected_records = options["expected_records"]
        target_isolate = options.get("isolate")
        target_assembly = options.get("assembly")

        failed_isolates = []

        logging.info("Starting gene import process.")

        try:
            # Load isolate-to-assembly mapping
            isolate_to_assembly_map = self.load_isolate_mapping(mapping_task_file)

            # Determine isolates to process
            if target_isolate:
                isolates = [target_isolate]
            elif target_assembly:
                isolates = [
                    isolate
                    for isolate, assembly in isolate_to_assembly_map.items()
                    if assembly == target_assembly
                ]
                if not isolates:
                    logging.warning(f"No isolates found for assembly: {target_assembly}")
                    return
            else:
                # Fetch list of isolates from FTP if none specified
                ftp = self.reconnect_ftp(ftp_server)
                ftp.cwd(ftp_directory)
                isolates = ftp.nlst()
                ftp.quit()

            logging.info(f"Found {len(isolates)} isolates to process.")

            # Process each isolate
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = {
                    executor.submit(
                        self.process_isolate, isolate, ftp_server, ftp_directory, isolate_to_assembly_map
                    ): isolate
                    for isolate in isolates
                }

                for future in futures:
                    isolate = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        logging.error(f"Error processing isolate {isolate}: {e}")
                        failed_isolates.append(isolate)

            logging.info("GFF files processed successfully.")

            # Import essentiality data and update gene index
            self.import_essentiality_data(essentiality_csv)

            logging.info("Essentiality data imported successfully.")

            # Validate total number of records
            self.validate_gene_index(expected_records)

        except Exception as e:
            logging.error(f"Error in the import process: {e}", exc_info=True)

        # Print failed isolates
        if failed_isolates:
            logging.warning(f"The following isolates failed to process: {failed_isolates}")
            print(f"\nFailed isolates:\n{failed_isolates}")
        else:
            logging.info("All isolates processed successfully.")

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

    def get_species_name(self, isolate_name):
        """ Extract species name from isolate name (assuming acronym-based species names). """
        species_acronym = isolate_name.split("_")[0]
        species_mapping = {
            "BU": "Bacteroides uniformis",
            "PV": "Phocaeicola vulgatus"
        }
        return species_mapping.get(species_acronym, None)

    def is_isolate_processed(self, isolate):
        """ Check if the isolate's data already exists in Elasticsearch. """
        response = GeneDocument.search().filter("term", isolate_name=isolate).execute()
        return response.hits.total.value > 0

    def process_isolate(self, isolate, ftp_server, ftp_directory, isolate_to_assembly_map, max_retries=5):
        """ Process GFF files for a given isolate with retry logic. """
        if self.is_isolate_processed(isolate):
            logging.info(f"Skipping already processed isolate: {isolate}")
            return

        for attempt in range(max_retries):
            try:
                logging.info(f"Processing isolate: {isolate} (Attempt {attempt + 1})")
                assembly_name = isolate_to_assembly_map.get(isolate)
                species_scientific_name = self.get_species_name(isolate)

                ftp = self.reconnect_ftp(ftp_server)
                isolate_path = f"{ftp_directory}/{isolate}/functional_annotation/merged_gff/"
                gff_files = ftp.nlst(isolate_path)
                ftp.quit()

                if not gff_files:
                    logging.warning(f"No GFF files found for isolate {isolate}")
                    return

                for gff_file in gff_files:
                    if gff_file.endswith("_annotations.gff"):
                        self.process_gff_file(gff_file, isolate, ftp_server, species_scientific_name, isolate)
                        self.update_strain_index(isolate, gff_file)

                logging.info(f"Successfully processed isolate: {isolate}")
                return

            except Exception as e:
                logging.error(f"Error processing isolate {isolate} on attempt {attempt + 1}: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    logging.error(f"Failed to process isolate {isolate} after {max_retries} attempts.")

    def process_gff_file(self, gff_file, isolate, ftp_server, species_scientific_name, isolate_name):
        """ Process GFF file and index gene data into Elasticsearch. """
        try:
            ftp = self.reconnect_ftp(ftp_server)
            local_gff_path = os.path.join("/tmp", os.path.basename(gff_file))

            # Check if the file exists before downloading
            try:
                ftp.size(gff_file)
            except ftplib.error_perm:
                logging.warning(f"File not found on FTP: {gff_file}")
                return

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

                    # Extract attributes
                    gene_name = attr_dict.get("Name")
                    locus_tag = attr_dict.get("locus_tag")
                    product = attr_dict.get("product")
                    # cog = attr_dict.get("cog", "").split(",") if "cog" in attr_dict else []
                    kegg = attr_dict.get("kegg", "").split(",") if "kegg" in attr_dict else []
                    pfam = attr_dict.get("pfam", "").split(",") if "pfam" in attr_dict else []
                    interpro = attr_dict.get("interpro", "").split(",")
                    dbxref_raw = attr_dict.get("Dbxref", "")
                    dbxref, uniprot_id, cog_id = self.parse_dbxref(dbxref_raw)
                    ec_number = attr_dict.get("eC_number")
                    alias = attr_dict.get("Alias", "").split(",") if "Alias" in attr_dict else []

                    # Extract cog functional categories
                    cog_funcats = attr_dict.get("cog", "").split(",") if "cog" in attr_dict else []

                    if not locus_tag:
                        continue

                    genes_to_index.append(
                        GeneDocument(
                            meta={"id": locus_tag},
                            gene_name=gene_name,
                            species_scientific_name=species_scientific_name,
                            species_acronym=self.get_species_acronym(species_scientific_name),
                            isolate_name=isolate_name,
                            seq_id=seq_id,
                            locus_tag=locus_tag,
                            product=product,
                            start=int(start),
                            end=int(end),
                            # cog=cog,
                            cog_funcats=cog_funcats,
                            kegg=kegg,
                            pfam=pfam,
                            interpro=interpro,
                            dbxref=dbxref,
                            uniprot_id=uniprot_id,
                            cog_id=cog_id,
                            ec_number=ec_number,
                            alias=alias
                        )
                    )

                    if len(genes_to_index) >= BATCH_SIZE:
                        bulk(connections.get_connection(), (doc.to_dict(include_meta=True) for doc in genes_to_index))
                        genes_to_index.clear()

            if genes_to_index:
                bulk(connections.get_connection(), (doc.to_dict(include_meta=True) for doc in genes_to_index))

        except Exception as e:
            logging.error(f"Error processing GFF file {gff_file}: {e}", exc_info=True)

        finally:
            if os.path.exists(local_gff_path):
                os.remove(local_gff_path)  # Ensures file is deleted even if errors occur

    def parse_dbxref(self, dbxref_string):
        """ Convert dbxref string into a structured nested field """
        dbxref_list = dbxref_string.split(",") if dbxref_string else []
        parsed_dbxref = []
        for entry in dbxref_list:
            if ":" in entry:
                db, ref = entry.split(":", 1)
                parsed_dbxref.append({"db": db, "ref": ref})
        return parsed_dbxref

    def update_strain_index(self, isolate, gff_file):
        """ Update the GFF file name in the strain index. """
        try:
            strain = StrainDocument.get(id=isolate, ignore=404)
            if strain:
                strain.gff_file = os.path.basename(gff_file)
                strain.save()
                logging.info(f"Updated strain_index for isolate {isolate} with GFF file: {gff_file}")
            else:
                logging.warning(f"Strain {isolate} not found in strain_index.")
        except Exception as e:
            logging.error(f"Error updating strain_index for isolate {isolate}: {e}")

    def import_essentiality_data(self, essentiality_csv):
        """ Import essentiality data and update genes in Elasticsearch efficiently. """
        try:
            if not os.path.exists(essentiality_csv):
                logging.error(f"Essentiality CSV file not found: {essentiality_csv}")
                return

            valid_strains = {"BU_ATCC8492", "PV_ATCC8482"}
            valid_essentiality_categories = {
                "essential": "Essential",
                "essential_liquid": "Essential Liquid",
                "essential_solid": "Essential Solid",
                "not_essential": "Not Essential",
                "unclear": "Unclear",
            }

            updates = []

            for chunk in pd.read_csv(essentiality_csv, chunksize=10000):
                for row in chunk.itertuples():
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

    def validate_gene_index(self, expected_count):
        """ Validate the total number of records in gene_index. """
        from elasticsearch_dsl import Search
        s = Search(index="gene_index")
        total_docs = s.count()

        if total_docs < expected_count:
            logging.warning(
                f"Expected {expected_count} records, but found {total_docs}. Missing {expected_count - total_docs} records.")
        else:
            logging.info(f"Gene index contains the expected number of records: {total_docs}")
