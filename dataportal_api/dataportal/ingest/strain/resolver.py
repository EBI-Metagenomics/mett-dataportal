from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple
import re

from elasticsearch_dsl import Search
from elasticsearch_dsl.connections import connections
from dataportal.models import StrainDocument

def isolate_lookup_key(s: str) -> str:
    """Uppercase and strip _, -, spaces for robust matching."""
    if not s:
        return s
    return re.sub(r"[_\-\s]", "", s).upper()

@dataclass
class StrainResolver:
    """
    Loads all strain ids once and resolves input names to a canonical _id.
    Keeps a reverse map of key->canonical_id, using heuristics to choose one.
    """
    index: str
    _key_to_ids: Dict[str, List[str]] = None
    _key_to_canonical: Dict[str, str] = None

    def load(self, source_fields: Iterable[str] = ("isolate_name", "isolate_key")) -> None:
        client = connections.get_connection()
        s = Search(using=client, index=self.index).source(list(source_fields)).params(size=1000)
        self._key_to_ids = {}
        for hit in s.scan():
            isolate_name = getattr(hit, "isolate_name", None) or hit.meta.id
            key = getattr(hit, "isolate_key", None) or isolate_lookup_key(isolate_name)
            self._key_to_ids.setdefault(key, []).append(hit.meta.id)
        # choose canonical for each key
        self._key_to_canonical = {k: self._choose_canonical(v) for k, v in self._key_to_ids.items()}

    @staticmethod
    def _choose_canonical(ids: List[str]) -> str:
        """
        Heuristic: prefer ids with underscores (more legible), then shorter, then lexicographically.
        """
        def score(x: str) -> tuple:
            return (('_' in x), -len(x), x.lower())
        return sorted(ids, key=score, reverse=True)[0]

    def canonicalize_if_known(self, incoming_name: str) -> Optional[str]:
        """
        Return the canonical isolate_id if the key is known.
        If unknown, return None (caller should skip).
        """
        key = isolate_lookup_key(incoming_name)
        if self._key_to_canonical and key in self._key_to_canonical:
            return self._key_to_canonical[key]
        return None

    @staticmethod
    def _normalize_preferred(s: str) -> str:
        # minimal normalization: replace '-' with '_' after the first segment
        if not s:
            return s
        s = s.strip()
        if "_" in s:
            head, tail = s.split("_", 1)
            return f"{head}_{tail.replace('-', '_')}"
        return s.replace("-", "_")

    def register_new(self, new_id: str) -> None:
        """If a new skeleton is created, record it so later rows resolve to the same id."""
        key = isolate_lookup_key(new_id)
        self._key_to_ids.setdefault(key, []).append(new_id)
        self._key_to_canonical[key] = self._choose_canonical(self._key_to_ids[key])
