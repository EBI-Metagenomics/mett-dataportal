from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("pyhmmer_search", "0009_alter_hmmerjob_database"),
    ]

    operations = [
        migrations.AddField(
            model_name="hmmerjob",
            name="species",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="hmmerjob",
            name="type_only",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="hmmerjob",
            name="isolate",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="hmmerjob",
            name="status",
            field=models.CharField(blank=True, default="", max_length=16),
        ),
        migrations.AddField(
            model_name="hmmerjob",
            name="result",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="hmmerjob",
            name="error",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="hmmerjob",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now, null=True
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="hmmerjob",
            name="finished_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="hmmerjob",
            name="database",
            field=models.CharField(
                choices=[
                    ("mett_proteins", "METT proteins"),
                    ("bu_type_strains", "Bacteroides uniformis Type Strains"),
                    ("bu_all", "Bacteroides uniformis All Strains"),
                    ("pv_type_strains", "Phocaeicola vulgatus Type Strains"),
                    ("pv_all", "Phocaeicola vulgatus All Strains"),
                    (
                        "bu_pv_type_strains",
                        "Bacteroides uniformis + Phocaeicola vulgatus Type Strains",
                    ),
                    (
                        "bu_pv_all",
                        "Bacteroides uniformis + Phocaeicola vulgatus All Strains",
                    ),
                    ("isolate_specific", "Isolate-Specific Database"),
                ],
                default="mett_proteins",
                max_length=32,
            ),
        ),
    ]
