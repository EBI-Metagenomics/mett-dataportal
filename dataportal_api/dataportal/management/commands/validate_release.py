from django.core.management.base import BaseCommand, CommandError

from dataportal.elasticsearch.names import INDEX_FAMILIES, IndexNameError, coerce_family
from dataportal.elasticsearch.release_ops import validate_release
from dataportal.elasticsearch.validation import manifest_family_key


class Command(BaseCommand):
    help = (
        "Compare Elasticsearch counts for a METT release against "
        "ReleaseManifest.expected_counts. Writes a VALIDATE audit row. "
        "Does not switch mett-current-* aliases."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--release",
            type=str,
            required=True,
            help="METT version token (v1, v2, …).",
        )
        parser.add_argument(
            "--family",
            action="append",
            dest="families",
            help="Limit to one or more family tokens. Repeatable.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the comparison without writing Postgres (no VALIDATE row, no status change).",
        )

    def handle(self, *args, **kwargs):
        release = kwargs["release"]
        families = kwargs.get("families")
        dry_run = kwargs.get("dry_run")

        if families:
            try:
                families = [coerce_family(f) for f in families]
            except IndexNameError as exc:
                raise CommandError(str(exc)) from exc

        self.stdout.write(
            f"Validating {release} against manifest expected_counts"
            f"{' (dry-run)' if dry_run else ''}..."
        )

        try:
            result = validate_release(
                release=release,
                families=families,
                actor="validate_release",
                dry_run=dry_run,
            )
        except (ValueError, IndexNameError) as exc:
            raise CommandError(str(exc)) from exc

        expected = result.get("expected") or {}
        actual = result.get("actual") or {}
        fams = families or list(INDEX_FAMILIES)
        checked = 0
        for family in fams:
            key = manifest_family_key(family)
            fam_expected = expected.get(key)
            if fam_expected is None:
                fam_expected = expected.get(family)
            fam_actual = actual.get(key) or {}
            if fam_actual.get("error"):
                self.stdout.write(self.style.ERROR(f"  {key}: {fam_actual['error']}"))
                continue
            alias = fam_actual.get("_alias") or f"mett-{release}-{family}"
            physical = ",".join(fam_actual.get("_physical") or [])
            self.stdout.write(f"  {alias} -> {physical}")
            if not isinstance(fam_expected, dict):
                total = fam_actual.get("total")
                if total is not None:
                    self.stdout.write(f"    total={total} (no expected checks)")
                continue
            for check, exp_val in fam_expected.items():
                if exp_val is None:
                    self.stdout.write(self.style.WARNING(f"    {key}.{check}: skipped (null)"))
                    continue
                act_val = fam_actual.get(check)
                if isinstance(exp_val, dict):
                    for sub_key, sub_exp in exp_val.items():
                        path = f"{key}.{check}.{str(sub_key).lower()}"
                        if sub_exp is None:
                            self.stdout.write(self.style.WARNING(f"    {path}: skipped (null)"))
                            continue
                        sub_act = (act_val or {}).get(str(sub_key).strip().lower(), 0)
                        checked += 1
                        self._print_check(path, sub_exp, sub_act)
                    continue
                checked += 1
                self._print_check(f"{key}.{check}", exp_val, act_val)

        mismatches = result.get("mismatches") or []
        skipped = result.get("skipped") or []
        if skipped:
            self.stdout.write(self.style.WARNING(f"\nSkipped {len(skipped)} null check(s)."))
        if mismatches:
            self.stdout.write(self.style.ERROR(f"\nFAIL: {len(mismatches)} mismatch(es)"))
            for row in mismatches:
                self.stdout.write(
                    self.style.ERROR(
                        f"  {row.get('path')}: expected {row.get('expected')} "
                        f"got {row.get('actual')} ({row.get('reason')})"
                    )
                )
            raise CommandError(
                f"Release {result.get('release')} validation failed "
                f"({len(mismatches)} mismatch(es)). Status={result.get('status')}."
            )

        suffix = " (dry-run, not recorded)" if dry_run else f". Status={result.get('status')}"
        self.stdout.write(self.style.SUCCESS(f"\nPASS: {checked} check(s) matched{suffix}."))
        if not dry_run:
            self.stdout.write(
                "VALIDATE row written on the release. "
                "mett-current-* is unchanged until promote_release."
            )

    def _print_check(self, path, expected, actual):
        try:
            ok = int(expected) == int(actual)
        except (TypeError, ValueError):
            ok = False
        line = f"    {path}: expected {expected}, actual {actual}"
        if ok:
            self.stdout.write(self.style.SUCCESS(f"{line} OK"))
        else:
            self.stdout.write(self.style.ERROR(f"{line} FAIL"))
