import ftplib
import json
import logging
import os
import csv
from concurrent.futures import ThreadPoolExecutor
import psycopg

# Configure logging
logging.basicConfig(
    filename='process_gff.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# Mapping task file path
mapping_task_file = './gff-assembly-prefixes.tsv'

# Load the mapping task file into a dictionary
isolate_to_assembly_map = {}
with open(mapping_task_file, mode='r') as file:
    reader = csv.DictReader(file, delimiter='\t')
    for row in reader:
        assembly_name = row['assembly'].replace('.fa', '')
        isolate_to_assembly_map[row['prefix']] = assembly_name

# FTP server details
ftp_server = 'ftp.ebi.ac.uk'
ftp_directory = '/pub/databases/mett/annotations/v1_2024-04-15/'

# Database query templates
gene_insert_query = """
INSERT INTO Gene (strain_id, gene_name, locus_tag, description, seq_id, cog, kegg, pfam, interpro, dbxref, ec_number, product, start_position, end_position, annotations)
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
WHERE assembly_name = %s
"""


# Function to list files in the directory and subdirectories
def list_files(ftp, path):
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


# Function to process a single GFF file
def process_gff_file(gff_file, isolate, strain_id):
    logging.info(f"Starting processing of {gff_file} for isolate {isolate}")
    try:
        with ftplib.FTP(ftp_server) as ftp:
            ftp.login()
            local_gff_path = os.path.join('/tmp', os.path.basename(gff_file))
            with open(local_gff_path, 'wb') as f:
                ftp.retrbinary(f"RETR {gff_file}", f.write)
            logging.info(f"Downloaded {gff_file} to {local_gff_path}")

        genes_to_insert = []
        ontology_terms = []

        with open(local_gff_path, 'r') as gff:
            sequence_started = False
            for line in gff:
                if line.startswith("##FASTA"):
                    logging.info(f"Ignoring assembly sequence in {gff_file}")
                    sequence_started = True
                    break

                if line.startswith("#"):
                    continue
                columns = line.strip().split("\t")
                if len(columns) != 9:
                    logging.warning(f"Skipping malformed line in {gff_file}: {line}")
                    continue

                seq_id, source, feature_type, start, end, score, strand, phase, attributes = columns
                if feature_type != 'gene':
                    continue
                attr_dict = dict(item.split('=') for item in attributes.split(';') if '=' in item)
                gene_name = attr_dict.get('Name')
                locus_tag = attr_dict.get('locus_tag')
                description = attr_dict.get('product')

                if not locus_tag:
                    logging.warning(f"Skipping gene without locus_tag in {gff_file}")
                    continue

                cog = attr_dict.get('cog')
                kegg = attr_dict.get('kegg')
                pfam = attr_dict.get('pfam')
                interpro = attr_dict.get('interpro')
                dbxref = attr_dict.get('Dbxref')
                ec_number = attr_dict.get('eC_number')
                product = attr_dict.get('product')

                annotations = {
                    "seq_id": seq_id,
                    "start_position": start,
                    "end_position": end,
                    "strand": strand,
                    "attributes": attr_dict
                }
                annotations_json = json.dumps(annotations)

                genes_to_insert.append((
                    strain_id[0], gene_name, locus_tag, description, seq_id, cog, kegg, pfam, interpro,
                    dbxref, ec_number, product, start, end, annotations_json
                ))

                if 'interpro' in attr_dict:
                    ontology_ids = attr_dict['interpro'].split(',')
                    for ont_id in ontology_ids:
                        ontology_terms.append((locus_tag, 'InterPro', ont_id.strip(), None))

        os.remove(local_gff_path)
        logging.info(f"Removed local GFF file {local_gff_path}")

        with psycopg.connect(
                dbname="postgres",
                user="postgres",
                password="pass123",
                host="localhost",
                port="5432"
        ) as conn:
            with conn.cursor() as cursor:
                if genes_to_insert:
                    cursor.executemany(gene_insert_query, genes_to_insert)
                    logging.info(f"Inserted {len(genes_to_insert)} genes from {gff_file}")
                else:
                    logging.warning(f"No genes to insert from {gff_file}")

                for gene_id_tuple, ontology_type, ontology_id, ontology_description in ontology_terms:
                    cursor.execute(
                        "SELECT id FROM Gene WHERE locus_tag = %s",
                        (gene_id_tuple,)
                    )
                    gene_id = cursor.fetchone()
                    if gene_id:
                        cursor.execute(ontology_insert_query,
                                       (gene_id[0], ontology_type, ontology_id, ontology_description))
                logging.info(f"Inserted ontology terms for {gff_file}")

                assembly_name = isolate_to_assembly_map.get(isolate)
                cursor.execute(update_strain_query, (os.path.basename(gff_file), assembly_name))
                logging.info(f"Updated Strain table with {os.path.basename(gff_file)} for assembly: {assembly_name}")

            conn.commit()

    except Exception as e:
        logging.error(f"Error processing GFF file {gff_file}: {e}", exc_info=True)


# Main function to process isolates
def process_isolate(isolate):
    logging.info(f"Processing isolate: {isolate}")
    assembly_name = isolate_to_assembly_map.get(isolate)
    try:
        with ftplib.FTP(ftp_server) as ftp:
            ftp.login()
            isolate_path = f"{ftp_directory}/{isolate}/functional_annotation/merged_gff/"
            gff_files_in_isolate = list_files(ftp, isolate_path)

        if not gff_files_in_isolate:
            logging.warning(f"No GFF files found for isolate {isolate}")
            return

        with psycopg.connect(
                dbname="postgres",
                user="postgres",
                password="pass123",
                host="localhost",
                port="5432"
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM Strain WHERE assembly_name = %s", (assembly_name,))
                strain_id = cursor.fetchone()

                if not strain_id:
                    logging.error(f"No strain_id found for isolate: {isolate}")
                    return

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for gff_file in gff_files_in_isolate:
                if gff_file.endswith('_annotations.gff'):
                    futures.append(executor.submit(process_gff_file, gff_file, isolate, strain_id))

            for future in futures:
                future.result()

    except Exception as e:
        logging.error(f"Error processing isolate {isolate}: {e}", exc_info=True)


# Main entry point
if __name__ == "__main__":
    try:
        with ftplib.FTP(ftp_server) as ftp:
            ftp.login()
            ftp.cwd(ftp_directory)
            isolates = ftp.nlst()
            logging.info(f"Found isolates: {isolates}")

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(process_isolate, isolate)
                for isolate in isolates
            ]
            for future in futures:
                future.result()

        logging.info("GFF files processed, and strain table updated.")

    except Exception as e:
        logging.error(f"Error in main processing: {e}", exc_info=True)
