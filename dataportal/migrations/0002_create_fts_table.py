from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('dataportal', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
                CREATE VIRTUAL TABLE IF NOT EXISTS species_fts USING fts5(
                    scientific_name, common_name,
                    content='species',
                    content_rowid='id'
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS strain_fts USING fts5(
                    isolate_name, strain_name, assembly_name, assembly_accession, fasta_file, gff_file,
                    content='strain',
                    content_rowid='id'
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS gene_fts USING fts5(
                    gene_id, gene_name, gene_symbol, locus_tag,
                    content='gene',
                    content_rowid='id'
                );
            ''',
            reverse_sql='''
                DROP TABLE IF EXISTS species_fts;
                DROP TABLE IF EXISTS strain_fts;
                DROP TABLE IF EXISTS gene_fts;
            '''
        ),
        # Remove the data population SQL commands
    ]
