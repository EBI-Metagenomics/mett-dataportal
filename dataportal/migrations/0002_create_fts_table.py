from django.db import migrations

def create_fts(apps, schema_editor):
    from dataportal.utils.fts_utils import FullTextSearchManager

    # Full-text search for Species
    species_fts_manager = FullTextSearchManager(
        table_name='species',
        fields=['scientific_name', 'common_name']
    )
    species_fts_manager.create_full_text_search_table()

    # Full-text search for Strain
    strain_fts_manager = FullTextSearchManager(
        table_name='strain',
        fields=['isolate_name', 'strain_name', 'assembly_name', 'assembly_accession', 'fasta_file', 'gff_file']
    )
    strain_fts_manager.create_full_text_search_table()

    # Full-text search for Gene
    gene_fts_manager = FullTextSearchManager(
        table_name='gene',
        fields=['gene_id', 'gene_name', 'gene_symbol', 'locus_tag']
    )
    gene_fts_manager.create_full_text_search_table()

class Migration(migrations.Migration):

    dependencies = [
        ('dataportal', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_fts),
    ]
