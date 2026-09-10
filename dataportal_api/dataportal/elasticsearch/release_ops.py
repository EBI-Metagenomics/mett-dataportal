"""Create physical release indexes, bind version aliases, adopt legacy indexes.

Does not switch `mett-current-*`. Promotion is a later command.
"""

from __future__ import annotations

import logging
from typing import Iterable, Optional

from django.db import transaction
from django.utils import timezone
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import connections

from dataportal.elasticsearch.indexing import ProjectIndexManager
from dataportal.elasticsearch.names import (
    INDEX_FAMILIES,
    coerce_family,
    concrete_index_names_from_resolve,
    current_alias_name,
    legacy_index_name,
    normalize_release,
    release_alias_name,
)
from dataportal.models.releases import (
    MettRelease,
    ReleaseChange,
    ReleaseIndex,
    ReleaseManifest,
)

logger = logging.getLogger(__name__)


def _es():
    return connections.get_connection()


def _as_dict(resp) -> dict:
    if resp is None:
        return {}
    if hasattr(resp, "body"):
        return resp.body
    if isinstance(resp, dict):
        return resp
    return dict(resp)


def resolve_concrete_indices(name: str) -> list[str]:
    """Follow aliases to concrete index names. Empty if `name` does not exist."""
    es = _es()
    try:
        payload = _as_dict(es.indices.resolve_index(name=name))
    except NotFoundError:
        return []
    except Exception as exc:
        msg = str(exc).lower()
        if "404" in msg or "not_found" in msg or "not found" in msg:
            return []
        raise
    return concrete_index_names_from_resolve(payload)


def index_or_alias_exists(name: str) -> bool:
    return bool(resolve_concrete_indices(name))


def add_alias(index_name: str, alias: str) -> None:
    """Point alias at concrete index(es). Follows `index_name` if it is itself an alias."""
    es = _es()
    wanted = resolve_concrete_indices(index_name)
    if not wanted:
        raise RuntimeError(
            f"Cannot add alias '{alias}': '{index_name}' does not resolve to a concrete index"
        )
    try:
        existing = es.indices.get_alias(name=alias)
        current = list(existing.keys()) if existing else []
    except NotFoundError:
        current = []
    except Exception as exc:
        msg = str(exc).lower()
        if "404" in msg or "not_found" in msg or "not found" in msg:
            current = []
        else:
            raise
    if set(current) == set(wanted):
        return
    if current and set(current) != set(wanted):
        raise RuntimeError(
            f"Alias '{alias}' already points at {current}; refusing to retarget to {wanted}. "
            "Promotion/rebuild commands retarget aliases after validation."
        )
    es.indices.update_aliases(
        body={"actions": [{"add": {"index": target, "alias": alias}} for target in wanted]}
    )


def get_or_create_release(version: str, *, actor: str = "") -> MettRelease:
    rel = normalize_release(version)
    if rel == "current":
        raise ValueError("Create a versioned release (v1, v2, …), not 'current'")
    obj, created = MettRelease.objects.get_or_create(
        version=rel,
        defaults={"status": MettRelease.Status.BUILDING},
    )
    if created:
        ReleaseManifest.objects.get_or_create(release=obj)
        logger.info("Created METT release %s", rel)
    return obj


def record_change(
    release: MettRelease,
    operation: str,
    *,
    domains: Optional[list] = None,
    payload: Optional[dict] = None,
    actor: str = "",
    status: str = ReleaseChange.Status.SUCCEEDED,
    error_message: str = "",
    before_counts: Optional[dict] = None,
    after_counts: Optional[dict] = None,
    validation_result: Optional[dict] = None,
) -> ReleaseChange:
    now = timezone.now() if status != ReleaseChange.Status.STARTED else None
    return ReleaseChange.objects.create(
        release=release,
        operation=operation,
        domains=domains or list(INDEX_FAMILIES),
        payload=payload or {},
        actor=actor,
        status=status,
        error_message=error_message,
        before_counts=before_counts,
        after_counts=after_counts,
        validation_result=validation_result,
        finished_at=now,
    )


def _upsert_release_index(
    release: MettRelease,
    family: str,
    physical: str,
    generation: int,
    adopted_legacy: bool,
) -> ReleaseIndex:
    alias = release_alias_name(release.version, family)
    obj, _ = ReleaseIndex.objects.update_or_create(
        release=release,
        family=family,
        defaults={
            "alias": alias,
            "physical_index": physical,
            "generation": generation,
            "adopted_legacy": adopted_legacy,
        },
    )
    return obj


@transaction.atomic
def create_release_indexes(
    *,
    release: str,
    generation: int,
    project: ProjectIndexManager,
    if_exists: str = "skip",
    families: Optional[Iterable[str]] = None,
    actor: str = "",
    bind_release_aliases: bool = True,
) -> dict[str, str]:
    """Create physical generation indexes and bind `mett-vN-{family}` aliases.

    Does not create or move `mett-current-*`.
    """
    rel = get_or_create_release(release, actor=actor)
    fams = [coerce_family(f) for f in (families or INDEX_FAMILIES)]
    created = project.create_physical_set(
        rel.version, generation, if_exists=if_exists, families=fams
    )
    if bind_release_aliases:
        for fam, concrete in created.items():
            add_alias(concrete, release_alias_name(rel.version, fam))
            _upsert_release_index(rel, fam, concrete, generation, adopted_legacy=False)
    else:
        for fam, concrete in created.items():
            _upsert_release_index(rel, fam, concrete, generation, adopted_legacy=False)

    if rel.status == MettRelease.Status.BUILDING:
        rel.status = MettRelease.Status.READY
        rel.save(update_fields=["status", "updated_at"])

    record_change(
        rel,
        "CREATE_INDEXES",
        domains=fams,
        payload={
            "generation": generation,
            "physical": created,
            "bind_aliases": bind_release_aliases,
        },
        actor=actor,
    )
    return created


@transaction.atomic
def adopt_legacy_indexes(
    *,
    release: str,
    generation: int = 1,
    families: Optional[Iterable[str]] = None,
    actor: str = "",
) -> dict[str, str]:
    """Point `mett-vN-{family}` at the concrete indexes behind existing `*_index` names.

    Live clusters often already have `species_index` as an alias. Elasticsearch
    cannot add an alias onto an alias, so we follow through to the concrete index.
    Does not switch `mett-current-*`.
    """
    rel = get_or_create_release(release, actor=actor)
    fams = [coerce_family(f) for f in (families or INDEX_FAMILIES)]
    adopted: dict[str, str] = {}
    missing: list[str] = []
    for fam in fams:
        legacy = legacy_index_name(fam)
        alias = release_alias_name(rel.version, fam)
        concrete = resolve_concrete_indices(legacy)
        if not concrete:
            missing.append(legacy)
            logger.warning("adopt-legacy: %s does not exist; skipping family %s", legacy, fam)
            continue
        add_alias(legacy, alias)
        physical = ",".join(concrete)
        _upsert_release_index(rel, fam, physical, generation, adopted_legacy=True)
        adopted[fam] = physical if physical == legacy else f"{legacy} -> {physical}"

    if not adopted:
        raise RuntimeError(
            "No legacy indexes found to adopt. Create them first or pass --release without --adopt-legacy."
        )

    if rel.status == MettRelease.Status.BUILDING:
        rel.status = MettRelease.Status.READY
        rel.save(update_fields=["status", "updated_at"])

    record_change(
        rel,
        "ADOPT_LEGACY",
        domains=list(adopted),
        payload={"generation": generation, "adopted": adopted, "missing": missing},
        actor=actor,
    )
    return adopted


def current_aliases_exist() -> bool:
    """True if at least one mett-current-* alias is present in ES."""
    try:
        return index_or_alias_exists(current_alias_name("species"))
    except Exception:
        return False


def _physical_mismatch(recorded: str, concrete: list[str]) -> bool:
    if not recorded or not concrete:
        return bool(concrete) != bool(recorded)
    recorded_names = {part.strip() for part in recorded.split(",") if part.strip()}
    return recorded_names != set(concrete)


def validate_release(
    *,
    release: str,
    families: Optional[Iterable[str]] = None,
    actor: str = "",
    dry_run: bool = False,
) -> dict:
    """Compare ES counts on `mett-vN-*` aliases against the release manifest.

    Writes a VALIDATE ReleaseChange. Sets status READY on pass or FAILED on
    mismatch when the release is still building/ready/failed. Does not move
    `mett-current-*`.
    """
    from dataportal.elasticsearch.validation import (
        collect_release_counts,
        compare_expected_counts,
        list_skipped_checks,
        manifest_family_key,
    )

    rel_token = normalize_release(release)
    if rel_token == "current":
        raise ValueError("Pass a version like v1, not 'current'")

    try:
        obj = MettRelease.objects.get(version=rel_token)
    except MettRelease.DoesNotExist as exc:
        raise ValueError(
            f"Release {rel_token} not found. Run create_es_index --release {rel_token} first."
        ) from exc

    try:
        manifest = obj.manifest
    except ReleaseManifest.DoesNotExist as exc:
        raise ValueError(
            "No release manifest. In Django admin, open the release and paste expected_counts."
        ) from exc

    expected = manifest.expected_counts or {}
    if not expected:
        raise ValueError(
            "Manifest expected_counts is empty. Paste inventory JSON in Django admin first."
        )

    fams = [coerce_family(f) for f in (families or INDEX_FAMILIES)]
    actual = collect_release_counts(rel_token, families=fams, expected=expected)
    mismatches = compare_expected_counts(expected, actual, families=fams)
    skipped = list_skipped_checks(expected, families=fams)

    indexes = {row.family: row for row in obj.indexes.all()}
    for family in fams:
        key = manifest_family_key(family)
        fam_actual = actual.get(key) or {}
        concrete = fam_actual.get("_physical") or []
        recorded = indexes.get(family)
        if recorded and _physical_mismatch(recorded.physical_index, list(concrete)):
            mismatches.append(
                {
                    "path": f"{key}._physical",
                    "expected": recorded.physical_index,
                    "actual": concrete,
                    "reason": "release alias does not point at the physical index recorded in Postgres",
                }
            )

    ok = not mismatches
    result = {
        "ok": ok,
        "release": rel_token,
        "mismatches": mismatches,
        "skipped": skipped,
    }

    if not dry_run:
        if obj.status in (
            MettRelease.Status.BUILDING,
            MettRelease.Status.READY,
            MettRelease.Status.FAILED,
        ):
            obj.status = MettRelease.Status.READY if ok else MettRelease.Status.FAILED
            obj.save(update_fields=["status", "updated_at"])
        record_change(
            obj,
            "VALIDATE",
            domains=fams,
            payload={"families": fams},
            actor=actor,
            status=ReleaseChange.Status.SUCCEEDED if ok else ReleaseChange.Status.FAILED,
            error_message="" if ok else f"{len(mismatches)} count mismatch(es)",
            before_counts=expected,
            after_counts=actual,
            validation_result=result,
        )

    result["actual"] = actual
    result["expected"] = expected
    result["status"] = obj.status
    return result
