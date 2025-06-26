from django.db import migrations
import datetime


def populate_initial_databases(apps, schema_editor):
    Database = apps.get_model("pyhmmer_search", "Database")

    # Hardcoded from HmmerJob.DbChoices
    entries = [
        ("bu_type_strains", "BU Type Strains"),
        ("bu_all", "BU All Strains"),
        ("pv_type_strains", "PV Type Strains"),
        ("pv_all", "PV All Strains"),
        ("bu_pv_type_strains", "BU+PV Type Strains"),
        ("bu_pv_all", "BU+PV All Strains"),
    ]

    for db_id, db_label in entries:
        Database.objects.update_or_create(
            id=db_id,
            defaults={
                "type": "seq",
                "name": db_label,
                "version": "1.0",
                "release_date": datetime.date.today(),
                "order": 0,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("pyhmmer_search", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(populate_initial_databases),
    ]
