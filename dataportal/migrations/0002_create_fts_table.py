from django.db import migrations

def create_fts(apps, schema_editor):
    from dataportal.utils import create_full_text_search_table
    create_full_text_search_table()

class Migration(migrations.Migration):

    dependencies = [
        ('dataportal', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_fts),
    ]
