from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from elasticsearch_dsl import Search
from elasticsearch_dsl.connections import connections

logger = logging.getLogger(__name__)


def isolate_lookup_key(s: str) -> str:
    """Uppercase and strip _, -, spaces for robust matching."""
    if not s:
        return s
    return re.sub(r"[_\-\s]", "", str(s)).upper()


@dataclass
class StrainResolver:
    """
    Loads all strain ids once and resolves input names to a canonical _id.
    Always normalizes isolate_name, isolate_key, and _id through isolate_lookup_key.
    """

    index: str
    _key_to_ids: Dict[str, List[str]] = field(default_factory=dict)
    _key_to_canonical: Dict[str, str] = field(default_factory=dict)
    loaded_count: int = 0

    def load(self, source_fields: Iterable[str] = ("isolate_name", "isolate_key")) -> None:
        self._key_to_ids = {}
        seen_ids: set[str] = set()
        search = Search(index=self.index).source(list(source_fields))
        for hit in search.scan():
            doc_id = hit.meta.id
            if not doc_id:
                continue
            seen_ids.add(doc_id)
            isolate_name = getattr(hit, "isolate_name", None) or doc_id
            isolate_key = getattr(hit, "isolate_key", None)
            for candidate in (doc_id, isolate_name, isolate_key):
                if not candidate:
                    continue
                key = isolate_lookup_key(candidate)
                if not key:
                    continue
                ids = self._key_to_ids.setdefault(key, [])
                if doc_id not in ids:
                    ids.append(doc_id)

        self.loaded_count = len(seen_ids)
        self._key_to_canonical = {k: self._choose_canonical(v) for k, v in self._key_to_ids.items()}
        try:
            es_count = connections.get_connection().count(index=self.index).get("count")
        except Exception:
            es_count = None
        logger.info(
            "StrainResolver loaded %s isolate(s) from %s (%s lookup keys, es _count=%s)",
            self.loaded_count,
            self.index,
            len(self._key_to_canonical),
            es_count,
        )
        if es_count is not None and es_count != self.loaded_count:
            logger.warning(
                "Scan loaded %s docs but %s._count is %s; isolate resolution may be incomplete.",
                self.loaded_count,
                self.index,
                es_count,
            )

    @staticmethod
    def _choose_canonical(ids: List[str]) -> str:
        def score(x: str) -> tuple:
            return ("_" in x, -len(x), x.lower())

        return sorted(ids, key=score, reverse=True)[0]

    def canonicalize_if_known(self, incoming_name: str) -> Optional[str]:
        if not incoming_name or not self._key_to_canonical:
            return None
        key = isolate_lookup_key(incoming_name)
        return self._key_to_canonical.get(key)

    def register_new(self, new_id: str) -> None:
        key = isolate_lookup_key(new_id)
        self._key_to_ids.setdefault(key, []).append(new_id)
        self._key_to_canonical[key] = self._choose_canonical(self._key_to_ids[key])
        self.loaded_count += 1
