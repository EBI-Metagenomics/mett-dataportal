"""Cross-release presence: query readable version aliases, never mett-current-*.

A promoted current alias points at the same physical index as mett-vN-{family}.
Including both would duplicate hits.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from dataportal.elasticsearch.names import (
    coerce_family,
    current_alias_name,
    release_alias_name,
)
from dataportal.models.releases import MettRelease

HISTORY_STATUSES = (
    MettRelease.Status.CURRENT,
    MettRelease.Status.ARCHIVED,
    MettRelease.Status.READY,
)

_PHYSICAL_INDEX_RE = re.compile(
    r"^mett-(v[1-9]\d*)-g\d{3}-(.+)$",
    re.IGNORECASE,
)
_ALIAS_INDEX_RE = re.compile(
    r"^mett-(v[1-9]\d*)-(.+)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ReleaseAlias:
    version: str
    status: str
    alias: str
    physical_index: str
    is_current: bool


def readable_aliases_for_family(family: str) -> list[ReleaseAlias]:
    """Version aliases for a family from Postgres. Omits mett-current-*."""
    qs = (
        MettRelease.objects.filter(status__in=HISTORY_STATUSES)
        .prefetch_related("indexes")
        .order_by("created_at")
    )
    return aliases_from_releases(list(qs), family)


def aliases_from_releases(releases, family: str) -> list[ReleaseAlias]:
    fam = coerce_family(family)
    current_alias = current_alias_name(fam)
    rows: list[ReleaseAlias] = []
    for rel in releases:
        index_row = next((idx for idx in rel.indexes.all() if idx.family == fam), None)
        alias = (index_row.alias if index_row else None) or release_alias_name(rel.version, fam)
        if alias == current_alias or alias.startswith("mett-current-"):
            continue
        physical = (index_row.physical_index if index_row else "") or ""
        rows.append(
            ReleaseAlias(
                version=rel.version,
                status=rel.status,
                alias=alias,
                physical_index=physical,
                is_current=rel.status == MettRelease.Status.CURRENT,
            )
        )
    return rows


def alias_names(rows: list[ReleaseAlias]) -> list[str]:
    names: list[str] = []
    for row in rows:
        if row.alias and row.alias not in names:
            names.append(row.alias)
    return names


def map_index_name_to_release(
    index_name: str,
    rows: list[ReleaseAlias],
    family: Optional[str] = None,
) -> Optional[ReleaseAlias]:
    """Map an ES hit `_index` (usually physical) back to a release row."""
    if not index_name:
        return None
    for row in rows:
        if index_name in (row.physical_index, row.alias):
            return row
    parsed = parse_release_from_index_name(index_name, family)
    if not parsed:
        return None
    version, _fam = parsed
    for row in rows:
        if row.version.lower() == version.lower():
            return row
    return None


def parse_release_from_index_name(
    index_name: str,
    family: Optional[str] = None,
) -> Optional[tuple[str, str]]:
    """Return (version, family) from mett-vN-gNNN-family or mett-vN-family. None for current."""
    name = (index_name or "").strip()
    if not name or name.startswith("mett-current-"):
        return None
    match = _PHYSICAL_INDEX_RE.match(name) or _ALIAS_INDEX_RE.match(name)
    if not match:
        return None
    version = match.group(1).lower()
    fam = match.group(2).lower()
    if family and coerce_family(family) != coerce_family(fam):
        return None
    return version, coerce_family(fam)


def version_sort_key(version: str) -> tuple[int, str]:
    token = (version or "").lower()
    if token.startswith("v"):
        try:
            return (int(token[1:]), token)
        except ValueError:
            return (0, token)
    return (0, token)


def dedupe_appearances(appearances: list[dict]) -> list[dict]:
    """One row per version; prefer is_current, then first seen. Sort by version number."""
    by_version: dict[str, dict] = {}
    for row in appearances:
        version = row.get("version")
        if not version:
            continue
        existing = by_version.get(version)
        if existing is None or (row.get("is_current") and not existing.get("is_current")):
            by_version[version] = row
    return sorted(by_version.values(), key=lambda item: version_sort_key(item["version"]))
