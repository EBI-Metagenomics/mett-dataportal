"""
Shared helpers for species/strain visibility filters used by genome and gene APIs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from dataportal.utils.constants import SPECIES_FIELD_ACRONYM_SHORT
from dataportal.utils.species_registry import get_enabled_species_acronyms
from dataportal.utils.strain_registry import get_enabled_isolate_names
from dataportal.utils.utils import split_comma_param


def resolve_enabled_species(requested: Optional[Sequence[str] | str] = None) -> List[str]:
    """
    Intersect requested species acronyms with the enabled set.
    When requested is empty/None, return all enabled acronyms.
    """
    enabled = get_enabled_species_acronyms()
    if not enabled:
        return []

    requested_list = (
        split_comma_param(requested)
        if isinstance(requested, str) or requested is None
        else [str(item).strip() for item in requested if str(item).strip()]
    )
    if not requested_list:
        return sorted(enabled)

    return [acronym for acronym in requested_list if acronym.strip().upper() in enabled]


def resolve_enabled_isolates(requested: Optional[Sequence[str] | str] = None) -> List[str]:
    """
    Intersect requested isolate names with the enabled set.
    When requested is empty/None, return all enabled isolates.
    Matching is case-insensitive; returned names use the registry casing.
    """
    enabled = get_enabled_isolate_names()
    if not enabled:
        return []

    by_lower = {name.lower(): name for name in enabled}
    requested_list = (
        split_comma_param(requested)
        if isinstance(requested, str) or requested is None
        else [str(item).strip() for item in requested if str(item).strip()]
    )
    if not requested_list:
        return sorted(enabled)

    resolved: List[str] = []
    for name in requested_list:
        match = by_lower.get(name.strip().lower())
        if match:
            resolved.append(match)
    return resolved


def apply_enabled_species_to_criteria(
    filter_criteria: Dict[str, Any],
    requested: Optional[Sequence[str] | str] = None,
) -> Dict[str, Any]:
    """
    Restrict filter_criteria species_acronym to enabled species.
    Uses an empty list when nothing is visible (callers should short-circuit).
    """
    existing = filter_criteria.get(SPECIES_FIELD_ACRONYM_SHORT)
    if requested is None and existing is not None:
        requested = existing
    filter_criteria[SPECIES_FIELD_ACRONYM_SHORT] = resolve_enabled_species(requested)
    return filter_criteria


def strain_not_disabled_clause() -> Dict[str, Any]:
    """
    ES clause that keeps strains where enabled is missing or true.
    Explicit enabled=false is excluded.
    """
    return {"bool": {"must_not": [{"term": {"enabled": False}}]}}


def gene_visibility_must_clauses(
    *,
    species_acronym: Optional[Sequence[str] | str] = None,
    isolates: Optional[Sequence[str] | str] = None,
) -> List[Dict[str, Any]]:
    """
    Build must clauses for gene/feature queries from enablement registries.
    Returns an empty list when the query should yield no hits (caller short-circuits).
    Actually returns clauses; use gene_visibility_blocks_all() for empty check.
    """
    species = resolve_enabled_species(species_acronym)
    if not species:
        return []

    clauses: List[Dict[str, Any]] = [
        {"terms": {SPECIES_FIELD_ACRONYM_SHORT: species}},
    ]

    requested_isolates = (
        split_comma_param(isolates)
        if isinstance(isolates, str) or isolates is None
        else [str(item).strip() for item in isolates if str(item).strip()]
    )
    if requested_isolates:
        allowed = resolve_enabled_isolates(requested_isolates)
        if not allowed:
            return []
        clauses.append({"terms": {"isolate_name": allowed}})
    else:
        enabled_isolates = resolve_enabled_isolates(None)
        if enabled_isolates:
            clauses.append({"terms": {"isolate_name": enabled_isolates}})

    return clauses


def gene_visibility_blocks_all(
    *,
    species_acronym: Optional[Sequence[str] | str] = None,
    isolates: Optional[Sequence[str] | str] = None,
) -> bool:
    """True when enablement filters exclude every possible hit."""
    return not gene_visibility_must_clauses(
        species_acronym=species_acronym,
        isolates=isolates,
    )
