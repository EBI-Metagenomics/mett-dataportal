# Generated by Django 5.2.1 on 2025-07-18 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pyhmmer_search", "0005_hmmerjob_bias_filter_alter_hmmerjob_database"),
    ]

    operations = [
        migrations.AlterField(
            model_name="database",
            name="name",
            field=models.CharField(max_length=128),
        ),
    ]
