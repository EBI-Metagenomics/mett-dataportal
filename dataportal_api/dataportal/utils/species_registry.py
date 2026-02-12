"""
In-memory cache of enabled species acronyms for fast filtering in gene/genome APIs.

Loaded at first use (or on server start if ensure_loaded() is called).
Updated when species are enabled/disabled via the admin APIs.
"""

import logging
import threading
from typing import Set

from dataportal.models.species import SpeciesDocument

logger = logging.getLogger(__name__)

_enabled_acronyms: Set[str] = set()
_lock = threading.RLock()
_loaded = False


def _load() -> None:
    """Load enabled species acronyms from Elasticsearch (sync)."""
    global _enabled_acronyms, _loaded
    with _lock:
        if _loaded:
            return
        try:
            search = SpeciesDocument.search().filter("term", enabled=True)
            search = search.source(["acronym"])
            response = search.execute()
            _enabled_acronyms = {hit.acronym for hit in response if getattr(hit, "acronym", None)}
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
            return
    # already loaded
    return


def get_enabled_species_acronyms() -> Set[str]:
    """Return a set of enabled species acronyms. Loads from ES on first call."""
    ensure_loaded()
    with _lock:
        return set(_enabled_acronyms)


def is_species_enabled(acronym: str) -> bool:
    """Return True if the species is enabled. Loads from ES on first call."""
    if not acronym:
        return False
    normalized = str(acronym).strip().upper()
    return normalized in get_enabled_species_acronyms()


def update_species_enabled(acronym: str, enabled: bool) -> None:
    """
    Update the in-memory cache after a species enable/disable in ES.
    Call this after successfully updating the species document.
    """
    global _enabled_acronyms
    normalized = str(acronym).strip().upper()
    with _lock:
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
