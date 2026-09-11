"""METT Elasticsearch release naming.

Scientist-visible names are aliases:

    mett-v1-species          ->  mett-v1-g001-species   (or a legacy index during cutover)
    mett-current-species     ->  whatever release is promoted

Physical indexes are generation-scoped and are not queried by the portal.
"""

from __future__ import annotations

import re
from typing import Iterable, Optional

CURRENT_TOKEN = "current"
RELEASE_HEADER = "X-METT-Release"
RELEASE_QUERY_PARAM = "release"
RELEASE_PATTERN = re.compile(r"^v[1-9]\d*$")

FAMILY_SPECIES = "species"
FAMILY_STRAINS = "strains"
FAMILY_STRAIN_EXPERIMENTS = "strain-experiments"
FAMILY_FEATURES = "features"
FAMILY_FEATURE_EXPERIMENTS = "feature-experiments"
FAMILY_PPI = "ppi"
FAMILY_OPERONS = "operons"
FAMILY_ORTHOLOGS = "orthologs"
FAMILY_FITNESS_CORRELATIONS = "fitness-correlations"

INDEX_FAMILIES: tuple[str, ...] = (
    FAMILY_SPECIES,
    FAMILY_STRAINS,
    FAMILY_STRAIN_EXPERIMENTS,
    FAMILY_FEATURES,
    FAMILY_FEATURE_EXPERIMENTS,
    FAMILY_PPI,
    FAMILY_OPERONS,
    FAMILY_ORTHOLOGS,
    FAMILY_FITNESS_CORRELATIONS,
)

FAMILY_TO_LEGACY_INDEX: dict[str, str] = {
    FAMILY_SPECIES: "species_index",
    FAMILY_STRAINS: "strain_index",
    FAMILY_STRAIN_EXPERIMENTS: "strain_experiment_index",
    FAMILY_FEATURES: "feature_index",
    FAMILY_FEATURE_EXPERIMENTS: "feature_experiment_index",
    FAMILY_PPI: "ppi_index",
    FAMILY_OPERONS: "operon_index",
    FAMILY_ORTHOLOGS: "ortholog_index",
    FAMILY_FITNESS_CORRELATIONS: "fitness_correlation_index",
}

LEGACY_INDEX_TO_FAMILY: dict[str, str] = {v: k for k, v in FAMILY_TO_LEGACY_INDEX.items()}


class IndexNameError(ValueError):
    """Invalid METT release, generation, or family token."""


def coerce_family(value: str) -> str:
    """Accept a family token or a legacy index name (`feature_index`)."""
    if not value:
        raise IndexNameError("Index family is required")
    token = value.strip().lower().replace("_", "-")
    if token.endswith("-index"):
        token = token[: -len("-index")]
    if token in INDEX_FAMILIES:
        return token
    legacy = value.strip()
    if legacy in LEGACY_INDEX_TO_FAMILY:
        return LEGACY_INDEX_TO_FAMILY[legacy]
    lowered = legacy.lower()
    if lowered in LEGACY_INDEX_TO_FAMILY:
        return LEGACY_INDEX_TO_FAMILY[lowered]
    raise IndexNameError(
        f"Unknown index family '{value}'. Expected one of: {', '.join(INDEX_FAMILIES)}"
    )


def normalize_release(value: Optional[str]) -> str:
    """Return `current` or `vN`. Empty / None means current."""
    if value is None:
        return CURRENT_TOKEN
    token = str(value).strip().lower()
    if token in ("", CURRENT_TOKEN):
        return CURRENT_TOKEN
    if not RELEASE_PATTERN.match(token):
        raise IndexNameError(
            f"Invalid METT release '{value}'. Use 'current' or a version like 'v1', 'v2'."
        )
    return token


def is_version_release(value: str) -> bool:
    return normalize_release(value) != CURRENT_TOKEN


def format_generation(generation: int) -> str:
    if not isinstance(generation, int) or generation < 1:
        raise IndexNameError("Generation must be an integer >= 1")
    return f"g{generation:03d}"


def physical_index_name(release: str, generation: int, family: str) -> str:
    """mett-v1-g001-species — never used as a portal read target."""
    rel = normalize_release(release)
    if rel == CURRENT_TOKEN:
        raise IndexNameError("Physical indexes belong to a METT version (v1, v2, …), not 'current'")
    return f"mett-{rel}-{format_generation(generation)}-{coerce_family(family)}"


def release_alias_name(release: str, family: str) -> str:
    """Stable alias for a METT version, or mett-current-{family} when release is current."""
    fam = coerce_family(family)
    rel = normalize_release(release)
    if rel == CURRENT_TOKEN:
        return current_alias_name(fam)
    return f"mett-{rel}-{fam}"


def current_alias_name(family: str) -> str:
    return f"mett-current-{coerce_family(family)}"


def all_release_aliases(release: str, families: Optional[Iterable[str]] = None) -> dict[str, str]:
    fams = tuple(families) if families is not None else INDEX_FAMILIES
    return {fam: release_alias_name(release, fam) for fam in fams}


def all_physical_names(
    release: str, generation: int, families: Optional[Iterable[str]] = None
) -> dict[str, str]:
    fams = tuple(families) if families is not None else INDEX_FAMILIES
    return {fam: physical_index_name(release, generation, fam) for fam in fams}


def legacy_index_name(family: str) -> str:
    return FAMILY_TO_LEGACY_INDEX[coerce_family(family)]


def concrete_index_names_from_resolve(payload: dict) -> list[str]:
    """Parse Elasticsearch `_resolve/index` into concrete index names (never aliases).

    Resolving an alias often returns the target only under `aliases[].indices`,
    with `indices` empty. Follow both.
    """
    names: list[str] = []
    for idx in (payload or {}).get("indices") or []:
        if isinstance(idx, dict) and idx.get("name"):
            names.append(idx["name"])
    for alias in (payload or {}).get("aliases") or []:
        if not isinstance(alias, dict):
            continue
        for target in alias.get("indices") or []:
            if target:
                names.append(target)
    seen: list[str] = []
    for name in names:
        if name and name not in seen:
            seen.append(name)
    return seen
