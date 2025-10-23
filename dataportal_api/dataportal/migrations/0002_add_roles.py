# Migration to add Role model and M2M relationship

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataportal', '0001_initial'),
    ]

    operations = [
        # Create Role model
        migrations.CreateModel(
            name="Role",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        help_text="Unique code for this role (e.g., 'proteomics', 'admin')",
                        max_length=50,
                        unique=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(help_text="Human-readable name for this role", max_length=100),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Detailed description of what this role grants access to",
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("core", "Core Access"),
                            ("experimental", "Experimental Data"),
                            ("interaction", "Interaction Data"),
                            ("advanced", "Advanced Features"),
                            ("custom", "Custom Role"),
                        ],
                        default="custom",
                        help_text="Category for organizing roles",
                        max_length=20,
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Whether this role is active and can be assigned to tokens",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, help_text="When this role was created"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, help_text="When this role was last updated"
                    ),
                ),
                (
                    "sort_order",
                    models.IntegerField(
                        default=0, help_text="Order for displaying roles (lower numbers first)"
                    ),
                ),
            ],
            options={
                "verbose_name": "Role",
                "verbose_name_plural": "Roles",
                "db_table": "roles",
                "ordering": ["category", "sort_order", "name"],
            },
        ),
        # Add indexes for Role
        migrations.AddIndex(
            model_name='role',
            index=models.Index(fields=['code'], name='idx_role_code'),
        ),
        migrations.AddIndex(
            model_name='role',
            index=models.Index(fields=['is_active'], name='idx_role_active'),
        ),
        migrations.AddIndex(
            model_name='role',
            index=models.Index(fields=['category'], name='idx_role_category'),
        ),
        # Add M2M field to APIToken
        migrations.AddField(
            model_name='apitoken',
            name='roles',
            field=models.ManyToManyField(
                blank=True,
                help_text="Roles assigned to this token",
                related_name="tokens",
                to="dataportal.role",
            ),
        ),
    ]

