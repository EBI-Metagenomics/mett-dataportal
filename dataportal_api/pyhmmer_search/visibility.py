"""Limit protein search to species the portal has enabled.

The PyHMMER search still reads the single protein database. This module only
applies the same enabled-species registry the genome and gene APIs use, at the
search and result endpoints.
"""

from __future__ import annotations

from dataportal.utils.enablement import resolve_enabled_species
from dataportal.utils.species_registry import get_enabled_species_acronyms, is_species_enabled


def species_acronym(label: str) -> str:
    """Species acronym on a locus tag such as BU_ATCC8492_00001."""
    return str(label or "").strip().split("_", 1)[0].upper()


def visible_hits(hits: list) -> list:
    """Drop hits whose locus tag belongs to a disabled species.

    When the registry has no enabled species, the hits are returned unchanged.
    That covers a registry that has not loaded, rather than hiding every hit.
    """
    if not isinstance(hits, list):
        return []
    enabled = get_enabled_species_acronyms()
    if not enabled:
        return hits
    return [
        hit
        for hit in hits
        if isinstance(hit, dict)
        and is_species_enabled(species_acronym(hit.get("target") or hit.get("seq_id") or ""))
    ]


def limit_search_species(requested: list[str] | None) -> list[str] | None:
    """Species list to store on a new search.

    None means the registry has no enabled species, so the request is left as
    the client sent it. An empty request becomes every enabled acronym. A
    request that names only disabled species becomes an empty list.
    """
    if not get_enabled_species_acronyms():
        return None
    return resolve_enabled_species(requested or [])


def visible_catalog(catalog: dict) -> dict:
    """Catalog entries the search form should offer."""
    if not get_enabled_species_acronyms():
        return catalog
    species = [
        item
        for item in catalog.get("species") or []
        if isinstance(item, dict) and is_species_enabled(item.get("acronym") or "")
    ]
    shortcuts = []
    for shortcut in catalog.get("shortcuts") or []:
        chosen = list(shortcut.get("species") or [])
        if not chosen:
            shortcuts.append(shortcut)
            continue
        kept = [acronym for acronym in chosen if is_species_enabled(acronym)]
        if kept:
            shortcuts.append({**shortcut, "species": kept})
    return {**catalog, "species": species, "shortcuts": shortcuts}
