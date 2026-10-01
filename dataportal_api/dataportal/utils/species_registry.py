"""
In-memory cache of enabled species acronyms for fast filtering in gene/genome APIs.

Loaded at first use (or on server start if ensure_loaded() is called).
Visibility is data-driven via species ingest; use rebuild() after reimport.
"""

from __future__ import annotations

import logging
import threading
from typing import Set

from dataportal.models.species import SpeciesDocument
from dataportal.utils.constants import MAX_RESULTS_PER_PAGE

logger = logging.getLogger(__name__)

_enabled_acronyms: Set[str] = set()
_lock = threading.RLock()
_loaded = False


def _normalize_acronym(acronym: str) -> str:
    return str(acronym).strip().upper()


def _load() -> None:
    """Load enabled species acronyms from Elasticsearch (sync)."""
    global _enabled_acronyms, _loaded
    with _lock:
        try:
            from dataportal.elasticsearch.resolver import resolve_read_index

            search = (
                SpeciesDocument.search(index=resolve_read_index("species"))
                .filter("term", enabled=True)
                .source(["acronym"])
                .extra(size=MAX_RESULTS_PER_PAGE)
            )
            response = search.execute()
            _enabled_acronyms = {
                _normalize_acronym(hit.acronym) for hit in response if getattr(hit, "acronym", None)
            }
            _loaded = True
            logger.info("Species registry loaded: %d enabled species", len(_enabled_acronyms))
        except Exception as e:
            logger.warning("Species registry load failed (will retry on next use): %s", e)
            _enabled_acronyms = set()
            _loaded = True  # avoid tight retry loop


def ensure_loaded() -> None:
    """Ensure the cache is populated. Safe to call at startup or before first use."""
    with _lock:
        if not _loaded:
            _load()


def get_enabled_species_acronyms() -> Set[str]:
    """Return a set of enabled species acronyms (uppercase). Loads from ES on first call."""
    ensure_loaded()
    with _lock:
        return set(_enabled_acronyms)


def is_species_enabled(acronym: str) -> bool:
    """Return True if the species is enabled. Loads from ES on first call."""
    if not acronym:
        return False
    return _normalize_acronym(acronym) in get_enabled_species_acronyms()


def update_species_enabled(acronym: str, enabled: bool) -> None:
    """
    Update the in-memory cache after a species enable/disable in ES.
    Prefer rebuild() after bulk ingest; this remains for targeted updates.
    """
    global _enabled_acronyms
    normalized = _normalize_acronym(acronym)
    with _lock:
        ensure_loaded()
        if enabled:
            _enabled_acronyms.add(normalized)
        else:
            _enabled_acronyms.discard(normalized)
        logger.info("Species registry updated: %s enabled=%s", normalized, enabled)


def invalidate_cache() -> None:
    """Force reload on next get_enabled_species_acronyms() / ensure_loaded()."""
    global _loaded
    with _lock:
        _loaded = False


def rebuild() -> int:
    """Force reload from Elasticsearch. Returns count of enabled species."""
    invalidate_cache()
    ensure_loaded()
    with _lock:
        return len(_enabled_acronyms)
