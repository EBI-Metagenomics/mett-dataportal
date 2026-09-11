from django.core.management.base import BaseCommand, CommandError

from dataportal.elasticsearch.names import INDEX_FAMILIES, IndexNameError, normalize_release
from dataportal.elasticsearch.release_ops import promote_release


class Command(BaseCommand):
    help = (
        "Point mett-current-* aliases at a validated METT release and mark it current. "
        "Archives any previous current release. This is the only command that moves "
        "mett-current-*."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--release",
            type=str,
            required=True,
            help="METT version token to make current (v1, v2, …).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print alias moves without updating Elasticsearch or Postgres.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Skip the ready-status and successful-VALIDATE checks.",
        )

    def handle(self, *args, **kwargs):
        release = kwargs["release"]
        dry_run = kwargs.get("dry_run")
        force = kwargs.get("force")

        try:
            normalize_release(release)
        except IndexNameError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            f"Promoting {release} to current"
            f"{' (dry-run)' if dry_run else ''}"
            f"{' (force)' if force else ''}..."
        )

        try:
            result = promote_release(
                release=release,
                actor="promote_release",
                dry_run=dry_run,
                force=force,
            )
        except (ValueError, IndexNameError, RuntimeError) as exc:
            raise CommandError(str(exc)) from exc

        mapping = result.get("mapping") or {}
        for family in INDEX_FAMILIES:
            row = mapping.get(family) or {}
            physical = ",".join(row.get("physical") or [])
            previous = ",".join(row.get("previous") or []) or "(none)"
            changed = "moved" if row.get("changed") else "unchanged"
            self.stdout.write(
                f"  {row.get('current_alias', family)}: {previous} -> {physical} ({changed})"
            )

        archived = result.get("archived") or []
        if archived:
            self.stdout.write(
                self.style.WARNING(f"  archived previous current: {', '.join(archived)}")
            )
        if result.get("warning"):
            self.stdout.write(self.style.WARNING(result["warning"]))

        n_actions = len(result.get("actions") or [])
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nDry-run: {n_actions} alias action(s) would run. "
                    "mett-current-* and Postgres were not changed."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"\nPromoted {result.get('release')} (status={result.get('status')}). "
                f"{n_actions} alias action(s) applied. "
                "Portal default now reads mett-current-*."
            )
        )
