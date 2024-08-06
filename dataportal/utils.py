from django.db import connection

def create_full_text_search_table():
    with connection.cursor() as cursor:
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS speciesdata_fts USING fts5(
                species, isolate_name, assembly_name, fasta_file, gff_file,
                content='speciesdata',
                content_rowid='id'
            );
        ''')

def update_full_text_search():
    with connection.cursor() as cursor:
        cursor.execute('''
            INSERT INTO speciesdata_fts(rowid, species, isolate_name, assembly_name, fasta_file, gff_file)
            SELECT id, species, isolate_name, assembly_name, fasta_file, gff_file FROM speciesdata;
        ''')
