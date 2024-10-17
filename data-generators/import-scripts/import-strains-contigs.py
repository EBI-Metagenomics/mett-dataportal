import ftplib
import os
import psycopg
from Bio import SeqIO  # For parsing FASTA files

# FTP server details
ftp_server = 'ftp.ebi.ac.uk'
ftp_directory = '/pub/databases/mett/all_hd_isolates/deduplicated_assemblies/'

# Database connection setup
conn = psycopg.connect(
    dbname="postgres",
    user="postgres",
    password="pass123",
    host="localhost",
    port="5432"
)

# Connect to the FTP server
ftp = ftplib.FTP(ftp_server)
ftp.login()

# Change to the target directory
ftp.cwd(ftp_directory)

# List files in the directory
files = ftp.nlst()

# Define insert query for Strain
strain_insert_query = """
INSERT INTO Strain (isolate_name, assembly_name, assembly_accession, fasta_file, species_id)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (assembly_accession) DO NOTHING
RETURNING id;
"""

# Define insert query for Contig
contig_insert_query = """
INSERT INTO Contig (strain_id, seq_id, length)
VALUES (%s, %s, %s)
ON CONFLICT DO NOTHING;
"""


# Helper function to extract acronym from isolate_name
def extract_acronym(isolate_name):
    return isolate_name.split('_')[0]  # Extracts acronym from the isolate_name (BU, PV, etc.)


# Starting point for sample assembly_accession
assembly_accession_start = 123456

# Filter for fasta files
fasta_files = [f for f in files if f.endswith('.fa')]

# Initialize the assembly accession counter
current_accession_number = assembly_accession_start

for file in fasta_files:
    assembly_name = os.path.splitext(file)[0]
    isolate_name = assembly_name.split('_NT')[0]
    assembly_accession = str(current_accession_number)  # Incrementing assembly accession number
    fasta_file = file

    # Extract acronym from isolate_name
    acronym = extract_acronym(isolate_name)

    # Fetch species_id based on the acronym
    with conn.cursor() as cursor:
        print(f'Processing {assembly_name}')
        cursor.execute("SELECT id FROM Species WHERE acronym = %s", (acronym,))
        species_id = cursor.fetchone()
        print(f'species_id: {species_id}')

        if species_id:
            # Insert strain and get strain_id
            cursor.execute(strain_insert_query, (
                isolate_name, assembly_name, assembly_accession, fasta_file, species_id[0]))
            strain_id = cursor.fetchone()[0]

            # Download the FASTA file for contig extraction
            with open(f'/tmp/{file}', 'wb') as fasta_local_file:
                ftp.retrbinary(f"RETR {file}", fasta_local_file.write)

            # Parse the FASTA file to extract contig information
            with open(f'/tmp/{file}', 'r') as fasta_local_file:
                for record in SeqIO.parse(fasta_local_file, "fasta"):
                    seq_id = record.id
                    length = len(record.seq)

                    # Insert contig information
                    cursor.execute(contig_insert_query, (strain_id, seq_id, length))
                    print(f'Inserted contig {seq_id} with length {length} for strain {isolate_name}')

            # Remove local fasta file after processing
            os.remove(f'/tmp/{file}')

    # Increment the assembly accession number
    current_accession_number += 1

    conn.commit()

# Close FTP and DB connections
ftp.quit()
conn.close()

print("Strain and contig data successfully inserted into the database.")
