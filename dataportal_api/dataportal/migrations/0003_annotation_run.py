from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dataportal", "0002_add_roles"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnnotationRun",
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
                ("isolate_name", models.CharField(db_index=True, max_length=255)),
                ("strain_id", models.CharField(blank=True, max_length=255, null=True)),
                ("release_label", models.CharField(max_length=64)),
                ("is_current", models.BooleanField(db_index=True, default=False)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("current", "Current"),
                            ("archived", "Archived"),
                            ("processing", "Processing"),
                        ],
                        default="processing",
                        max_length=32,
                    ),
                ),
                (
                    "mettannotator_version",
                    models.CharField(blank=True, default="", max_length=64),
                ),
                (
                    "pipeline_version",
                    models.CharField(blank=True, default="", max_length=64),
                ),
                (
                    "doc_link",
                    models.URLField(blank=True, default="", max_length=1024),
                ),
                ("comments", models.TextField(blank=True, default="")),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "es_feature_index",
                    models.CharField(
                        help_text="Concrete Elasticsearch feature index for this release (e.g. feature_index-1.0).",
                        max_length=255,
                    ),
                ),
                ("gff_file", models.CharField(blank=True, default="", max_length=512)),
                (
                    "gff_ftp_template",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="URL template with optional {} for isolate_name, or a full GFF URL.",
                        max_length=1024,
                    ),
                ),
            ],
            options={
                "db_table": "annotation_run",
                "ordering": ["-is_current", "-processed_at", "-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="annotationrun",
            constraint=models.UniqueConstraint(
                fields=("isolate_name", "release_label"),
                name="uniq_isolate_annotation_release",
            ),
        ),
        migrations.AddConstraint(
            model_name="annotationrun",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_current", True)),
                fields=("isolate_name",),
                name="uniq_current_annotation_per_isolate",
            ),
        ),
    ]
