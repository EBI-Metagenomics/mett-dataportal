"""PostgreSQL models for METT Elasticsearch release metadata.

A scientist-visible version (`v1`) is a complete set of index aliases.
Physical Elasticsearch generations can change behind those aliases.
Expected counts live on the release manifest, not in Nextflow.
"""

from django.db import models

from dataportal.elasticsearch.names import INDEX_FAMILIES, current_alias_name, release_alias_name


class MettRelease(models.Model):
    """One scientist-visible METT data release (v1, v2, …)."""

    class Status(models.TextChoices):
        BUILDING = "building", "Building"
        READY = "ready", "Ready (not current)"
        CURRENT = "current", "Current"
        ARCHIVED = "archived", "Archived"
        FAILED = "failed", "Failed"
        PRUNED = "pruned", "Pruned"

    version = models.CharField(
        max_length=16,
        unique=True,
        help_text="Scientist-visible version token, e.g. v1",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.BUILDING,
        db_index=True,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    promoted_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "mett_releases"
        ordering = ["-created_at"]
        verbose_name = "METT release"
        verbose_name_plural = "METT releases"

    def __str__(self) -> str:
        return f"{self.version} ({self.status})"

    @property
    def is_writable(self) -> bool:
        return self.status in (self.Status.BUILDING, self.Status.READY, self.Status.CURRENT)

    @property
    def is_readable(self) -> bool:
        return self.status in (
            self.Status.READY,
            self.Status.CURRENT,
            self.Status.ARCHIVED,
            self.Status.BUILDING,
        )


class ReleaseIndex(models.Model):
    """One family in a release: alias + current physical generation."""

    release = models.ForeignKey(MettRelease, on_delete=models.CASCADE, related_name="indexes")
    family = models.CharField(max_length=64, help_text="Family token, e.g. features")
    alias = models.CharField(max_length=128, help_text="Stable alias, e.g. mett-v1-features")
    physical_index = models.CharField(
        max_length=128,
        help_text="Concrete ES index the alias currently points at",
    )
    generation = models.PositiveIntegerField(default=1)
    adopted_legacy = models.BooleanField(
        default=False,
        help_text="True when the alias still points at a pre-release *_index",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "mett_release_indexes"
        unique_together = [("release", "family")]
        ordering = ["family"]
        verbose_name = "Release index"
        verbose_name_plural = "Release indexes"

    def __str__(self) -> str:
        return f"{self.alias} -> {self.physical_index}"

    def save(self, *args, **kwargs):
        if self.release_id and self.family and not self.alias:
            self.alias = release_alias_name(self.release.version, self.family)
        super().save(*args, **kwargs)


class ReleaseManifest(models.Model):
    """Inputs and expected counts for a release. Validation compares against this."""

    release = models.OneToOneField(MettRelease, on_delete=models.CASCADE, related_name="manifest")
    inputs = models.JSONField(
        default=dict,
        blank=True,
        help_text="Source paths, FTP roots, checksums, isolate lists",
    )
    expected_counts = models.JSONField(
        default=dict,
        blank=True,
        help_text="Inventory expectations, e.g. species_total, species_enabled",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "mett_release_manifests"
        verbose_name = "Release manifest"
        verbose_name_plural = "Release manifests"

    def __str__(self) -> str:
        return f"manifest {self.release.version}"


class ReleaseChange(models.Model):
    """Provenance for every mutation of a release, including in-place current updates."""

    class Status(models.TextChoices):
        STARTED = "started", "Started"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    release = models.ForeignKey(MettRelease, on_delete=models.CASCADE, related_name="changes")
    operation = models.CharField(
        max_length=64,
        help_text="NEW_RELEASE, ADOPT_LEGACY, ADD_STRAIN, REPLACE_FEATURE_SET, …",
    )
    domains = models.JSONField(default=list, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    actor = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.STARTED)
    before_counts = models.JSONField(null=True, blank=True)
    after_counts = models.JSONField(null=True, blank=True)
    validation_result = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "mett_release_changes"
        ordering = ["-started_at"]
        verbose_name = "Release change"
        verbose_name_plural = "Release changes"

    def __str__(self) -> str:
        return f"{self.operation} {self.release.version} ({self.status})"


def current_alias_for(family: str) -> str:
    return current_alias_name(family)


# Touch INDEX_FAMILIES so imports stay discoverable for admin/forms.
KNOWN_FAMILIES = INDEX_FAMILIES
