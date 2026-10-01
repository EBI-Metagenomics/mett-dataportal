"""
In-memory cache of enabled isolate names for genome/gene visibility filtering.

Loaded at first use or via ensure_loaded() / rebuild(). Missing `enabled` on a
strain document is treated as enabled (backward compatible).
"""

from __future__ import annotations

import logging
import threading
from typing import Set

from dataportal.models.strains import StrainDocument
from dataportal.utils.constants import MAX_RESULTS_PER_PAGE

logger = logging.getLogger(__name__)

_enabled_isolates: Set[str] = set()
_lock = threading.RLock()
_loaded = False


def _is_enabled_value(value) -> bool:
    """Missing/None means enabled; only explicit False disables."""
    return value is not False


def _load() -> None:
    global _enabled_isolates, _loaded
    with _lock:
        try:
            from dataportal.elasticsearch.resolver import resolve_read_index

            search = (
                StrainDocument.search(index=resolve_read_index("strains"))
                .source(["isolate_name", "enabled"])
                .extra(size=MAX_RESULTS_PER_PAGE)
            )
            response = search.execute()
            enabled: Set[str] = set()
            for hit in response:
                isolate = getattr(hit, "isolate_name", None)
                if not isolate:
                    continue
                if _is_enabled_value(getattr(hit, "enabled", None)):
                    enabled.add(str(isolate))
            _enabled_isolates = enabled
            _loaded = True
            logger.info("Strain registry loaded: %d enabled isolates", len(_enabled_isolates))
        except Exception as e:
            logger.warning("Strain registry load failed (will retry on next use): %s", e)
            _enabled_isolates = set()
            _loaded = True


def ensure_loaded() -> None:
    with _lock:
        if not _loaded:
            _load()


def get_enabled_isolate_names() -> Set[str]:
    ensure_loaded()
    with _lock:
        return set(_enabled_isolates)


def is_isolate_enabled(isolate_name: str) -> bool:
    if not isolate_name:
        return False
    enabled = get_enabled_isolate_names()
    if not enabled:
        return False
    needle = str(isolate_name).strip().lower()
    return any(name.lower() == needle for name in enabled)


def invalidate_cache() -> None:
    global _loaded
    with _lock:
        _loaded = False


def rebuild() -> int:
    """Force reload from Elasticsearch. Returns count of enabled isolates."""
    invalidate_cache()
    ensure_loaded()
    with _lock:
        return len(_enabled_isolates)
