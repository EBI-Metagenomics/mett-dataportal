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
