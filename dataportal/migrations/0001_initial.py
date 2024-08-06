from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="SpeciesData",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("species", models.CharField(max_length=255)),
                ("isolate_name", models.CharField(max_length=255)),
                ("assembly_name", models.CharField(max_length=255)),
                ("fasta_file", models.CharField(max_length=255)),
                ("gff_file", models.CharField(max_length=255)),
            ],
            options={
                "db_table": "speciesdata",
            },
        ),
    ]
