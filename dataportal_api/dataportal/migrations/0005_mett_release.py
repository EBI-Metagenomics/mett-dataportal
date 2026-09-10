from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("dataportal", "0004_delete_annotation_run"),
    ]

    operations = [
        migrations.CreateModel(
            name="MettRelease",
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
                (
                    "version",
                    models.CharField(
                        help_text="Scientist-visible version token, e.g. v1",
                        max_length=16,
                        unique=True,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("building", "Building"),
                            ("ready", "Ready (not current)"),
                            ("current", "Current"),
                            ("archived", "Archived"),
                            ("failed", "Failed"),
                            ("pruned", "Pruned"),
                        ],
                        db_index=True,
                        default="building",
                        max_length=16,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("promoted_at", models.DateTimeField(blank=True, null=True)),
                ("archived_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "METT release",
                "verbose_name_plural": "METT releases",
                "db_table": "mett_releases",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ReleaseManifest",
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
                (
                    "inputs",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Source paths, FTP roots, checksums, isolate lists",
                    ),
                ),
                (
                    "expected_counts",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Inventory expectations, e.g. species_total, species_enabled",
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "release",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="manifest",
                        to="dataportal.mettrelease",
                    ),
                ),
            ],
            options={
                "verbose_name": "Release manifest",
                "verbose_name_plural": "Release manifests",
                "db_table": "mett_release_manifests",
            },
        ),
        migrations.CreateModel(
            name="ReleaseIndex",
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
                (
                    "family",
                    models.CharField(help_text="Family token, e.g. features", max_length=64),
                ),
                (
                    "alias",
                    models.CharField(
                        help_text="Stable alias, e.g. mett-v1-features", max_length=128
                    ),
                ),
                (
                    "physical_index",
                    models.CharField(
                        help_text="Concrete ES index the alias currently points at",
                        max_length=128,
                    ),
                ),
                ("generation", models.PositiveIntegerField(default=1)),
                (
                    "adopted_legacy",
                    models.BooleanField(
                        default=False,
                        help_text="True when the alias still points at a pre-release *_index",
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "release",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="indexes",
                        to="dataportal.mettrelease",
                    ),
                ),
            ],
            options={
                "verbose_name": "Release index",
                "verbose_name_plural": "Release indexes",
                "db_table": "mett_release_indexes",
                "ordering": ["family"],
                "unique_together": {("release", "family")},
            },
        ),
        migrations.CreateModel(
            name="ReleaseChange",
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
                (
                    "operation",
                    models.CharField(
                        help_text="NEW_RELEASE, ADOPT_LEGACY, ADD_STRAIN, REPLACE_FEATURE_SET, …",
                        max_length=64,
                    ),
                ),
                ("domains", models.JSONField(blank=True, default=list)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("actor", models.CharField(blank=True, max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("started", "Started"),
                            ("succeeded", "Succeeded"),
                            ("failed", "Failed"),
                        ],
                        default="started",
                        max_length=16,
                    ),
                ),
                ("before_counts", models.JSONField(blank=True, null=True)),
                ("after_counts", models.JSONField(blank=True, null=True)),
                ("validation_result", models.JSONField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                (
                    "release",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="changes",
                        to="dataportal.mettrelease",
                    ),
                ),
            ],
            options={
                "verbose_name": "Release change",
                "verbose_name_plural": "Release changes",
                "db_table": "mett_release_changes",
                "ordering": ["-started_at"],
            },
        ),
    ]
