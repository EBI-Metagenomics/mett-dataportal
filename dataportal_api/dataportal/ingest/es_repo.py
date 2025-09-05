from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple, List, Dict, Any

from elasticsearch import NotFoundError
from elasticsearch.helpers import bulk, BulkIndexError
from elasticsearch_dsl import connections

from dataportal.models import StrainDocument, FeatureDocument


# -----------------------------
# Repositories
# -----------------------------

@dataclass
class StrainIndexRepository:
    """
    Read/write StrainDocument to a specific *concrete* ES index.
    Use this if you need to bypass an alias and write to a versioned index.
    """
    concrete_index: str

    def get(self, isolate_name: str) -> Optional[StrainDocument]:
        try:
            # ignore=404 returns None instead of raising
            return StrainDocument.get(
                id=isolate_name,
                index=self.concrete_index,
                ignore=404,
            )
        except NotFoundError:
            return None

    def save(self, doc: StrainDocument) -> None:
        doc.save(index=self.concrete_index)


@dataclass
class FeatureIndexRepository:
    """
    Read/write FeatureDocument to a specific *concrete* ES index.
    Use this for versioned feature indices (e.g., feature_index_vX).
    """
    concrete_index: str

    def get(self, feature_id: str) -> Optional[FeatureDocument]:
        try:
            return FeatureDocument.get(
                id=feature_id,
                index=self.concrete_index,
                ignore=404,
            )
        except NotFoundError:
            return None

    def save(self, doc: FeatureDocument) -> None:
        doc.save(index=self.concrete_index)


# -----------------------------
# Bulk utilities
# -----------------------------

def bulk_exec(
        actions: Iterable[Dict[str, Any]],
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Execute a bulk request using the default elasticsearch_dsl connection.
    Returns (success_count, failures_list). Does not raise on partial failures.
    """
    # materialize once so we can check emptiness and reuse
    if not isinstance(actions, list):
        actions = list(actions)

    if not actions:
        return 0, []

    try:
        success, failures = bulk(
            connections.get_connection(),
            actions,
            raise_on_error=False,
        )
        if failures:
            print(f"[es_repo] Bulk failures: {len(failures)} (first 3 shown)")
            for f in failures[:3]:
                print(f"  -> {f}")
        return success, failures
    except BulkIndexError as e:
        errs = getattr(e, "errors", [])
        print(f"[es_repo] BulkIndexError with {len(errs)} errors (first 3 shown)")
        for f in errs[:3]:
            print(f"  -> {f}")
        return 0, errs


# -----------------------------
# Painless script snippets
# -----------------------------
# These are used by the ingestion flows.

SCRIPT_APPEND_NESTED = """
if (ctx._source[params.field] == null) { ctx._source[params.field] = []; }
ctx._source[params.field].add(params.entry);
"""

SCRIPT_APPEND_AND_SET_FLAG = """
if (ctx._source[params.field] == null) { ctx._source[params.field] = []; }
ctx._source[params.field].add(params.entry);
ctx._source[params.flag_field] = true;
"""

SCRIPT_APPEND_NESTED_DEDUP_BY_KEYS = """
if (ctx._source[params.field] == null) { ctx._source[params.field] = []; }
boolean exists = false;
for (item in ctx._source[params.field]) {
  boolean same = true;
  for (k in params.keys) {
    if (item[k] == null && params.entry[k] == null) { continue; }
    if (item[k] != params.entry[k]) { same = false; break; }
  }
  if (same) { exists = true; break; }
}
if (!exists) { ctx._source[params.field].add(params.entry); }
"""


# -----------------------------
# Optional: small helper for batching
# -----------------------------
def iter_batches(iterable: Iterable[Any], size: int):
    """Yield lists of up to `size` from an iterable."""
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch
