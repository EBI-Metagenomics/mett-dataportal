from django.db import migrations

def create_fts(apps, schema_editor):
    from dataportal.utils.fts_utils import FullTextSearchManager
    fts_manager = FullTextSearchManager(
        table_name='speciesdata',
        fields=['species', 'isolate_name', 'assembly_name', 'fasta_file', 'gff_file']
    )
    fts_manager.create_full_text_search_table()

class Migration(migrations.Migration):

    dependencies = [
        ('dataportal', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_fts),
    ]
