# Migration for existing api_tokens table
# This assumes api_tokens table already exists from previous setup

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        # Create APIToken model but don't create table (already exists)
        migrations.CreateModel(
            name="APIToken",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Unique name/identifier for this token (e.g., 'stakeholder1', 'reviewer_john')",
                        max_length=255,
                        unique=True,
                    ),
                ),
                ("token", models.TextField(help_text="The actual JWT token string", unique=True)),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Optional description of what this token is used for",
                        null=True,
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Whether this token is currently active and can be used for authentication",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, help_text="When this token was created"
                    ),
                ),
                (
                    "expires_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When this token expires (null = never expires)",
                        null=True,
                    ),
                ),
                (
                    "last_used_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When this token was last used for authentication",
                        null=True,
                    ),
                ),
                (
                    "created_by",
                    models.CharField(
                        blank=True, help_text="Who created this token", max_length=255, null=True
                    ),
                ),
            ],
            options={
                "verbose_name": "API Token",
                "verbose_name_plural": "API Tokens",
                "db_table": "api_tokens",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["token"], name="idx_api_token"),
                    models.Index(fields=["is_active"], name="idx_api_token_active"),
                ],
            },
        ),
    ]

