"""PostgreSQL model for per-genome annotation processing runs."""

from django.db import models


class AnnotationRun(models.Model):
    STATUS_CURRENT = "current"
    STATUS_ARCHIVED = "archived"
    STATUS_PROCESSING = "processing"
    STATUS_CHOICES = [
        (STATUS_CURRENT, "Current"),
        (STATUS_ARCHIVED, "Archived"),
        (STATUS_PROCESSING, "Processing"),
    ]

    isolate_name = models.CharField(max_length=255, db_index=True)
    strain_id = models.CharField(max_length=255, blank=True, null=True)
    release_label = models.CharField(max_length=64)
    is_current = models.BooleanField(default=False, db_index=True)
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_PROCESSING,
    )
    mettannotator_version = models.CharField(max_length=64, blank=True, default="")
    pipeline_version = models.CharField(max_length=64, blank=True, default="")
    doc_link = models.URLField(max_length=1024, blank=True, default="")
    comments = models.TextField(blank=True, default="")
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    es_feature_index = models.CharField(
        max_length=255,
        help_text="Concrete Elasticsearch feature index for this release (e.g. feature_index-1.0).",
    )
    gff_file = models.CharField(max_length=512, blank=True, default="")
    gff_ftp_template = models.CharField(
        max_length=1024,
        blank=True,
        default="",
        help_text="URL template with optional {} for isolate_name, or a full GFF URL.",
    )

    class Meta:
        db_table = "annotation_run"
        ordering = ["-is_current", "-processed_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["isolate_name", "release_label"],
                name="uniq_isolate_annotation_release",
            ),
            models.UniqueConstraint(
                fields=["isolate_name"],
                condition=models.Q(is_current=True),
                name="uniq_current_annotation_per_isolate",
            ),
        ]

    def __str__(self) -> str:
        current = "current" if self.is_current else self.status
        return f"{self.isolate_name} @ {self.release_label} ({current})"

    def gff_url(self) -> str | None:
        if not self.gff_file and "{}" not in (self.gff_ftp_template or ""):
            return self.gff_ftp_template or None
        template = self.gff_ftp_template or ""
        if not template:
            return None
        try:
            base = template.format(self.isolate_name)
        except (IndexError, KeyError):
            base = template
        if self.gff_file:
            return f"{base.rstrip('/')}/{self.gff_file}"
        return base or None
