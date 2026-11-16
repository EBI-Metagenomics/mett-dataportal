from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple, List, Dict, Any

import logging

from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.helpers import bulk as es_bulk, BulkIndexError, bulk
from elasticsearch_dsl import connections

from dataportal.models import (
    StrainDocument,
    FeatureDocument,
    SpeciesDocument,
    StrainExperimentDocument,
    FeatureExperimentDocument,
    ProteinProteinDocument,
    OperonDocument,
    OrthologDocument,
    GeneFitnessCorrelationDocument,
)


logger = logging.getLogger(__name__)

# Fields added for PPI v4. Applied onto an existing index without retargeting
# consensus_score, which may already be mapped as scaled_float.
PPI_V4_MAPPING_PROPERTIES = {
    "raw_consensus_score": {"type": "double"},
    "q_ppi": {"type": "double"},
    "q_chemical_genetic": {"type": "double"},
    "q_coexpression": {"type": "double"},
    "q_operons": {"type": "double"},
    "q_metabolic": {"type": "double"},
    "n_evidence_types": {"type": "integer"},
    "n_networks_total": {"type": "integer"},
    "n_ppi": {"type": "integer"},
    "n_chemical_genetic": {"type": "integer"},
    "n_coexpression": {"type": "integer"},
    "n_operons": {"type": "integer"},
    "n_metabolic": {"type": "integer"},
    "has_ppi": {"type": "boolean"},
    "has_chemical_genetic": {"type": "boolean"},
    "has_coexpression": {"type": "boolean"},
    "has_operons": {"type": "boolean"},
    "has_metabolic": {"type": "boolean"},
}


# -----------------------------
# Repositories
# -----------------------------


@dataclass
class SpeciesIndexRepository:
    """
    Read/write SpeciesDocument to a specific *concrete* ES index
    (e.g., 'species_index' or versioned).
    """

    concrete_index: str

    def get(self, acronym: str) -> Optional[SpeciesDocument]:
        try:
            return SpeciesDocument.get(id=acronym, index=self.concrete_index, ignore=404)
        except NotFoundError:
            return None

    def save(self, doc: SpeciesDocument) -> None:
        doc.save(index=self.concrete_index)


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
class StrainExperimentIndexRepository:
    """Read/write StrainExperimentDocument to a concrete strain-experiment index."""

    concrete_index: str

    def get(self, isolate_name: str) -> Optional[StrainExperimentDocument]:
        try:
            return StrainExperimentDocument.get(
                id=isolate_name,
                index=self.concrete_index,
                ignore=404,
            )
        except NotFoundError:
            return None

    def save(self, doc: StrainExperimentDocument) -> None:
        doc.save(index=self.concrete_index)


@dataclass
class FeatureExperimentIndexRepository:
    """Read/write FeatureExperimentDocument to a concrete experiment index."""

    concrete_index: str

    def get(self, feature_id: str) -> Optional[FeatureExperimentDocument]:
        try:
            return FeatureExperimentDocument.get(
                id=feature_id,
                index=self.concrete_index,
                ignore=404,
            )
        except NotFoundError:
            return None

    def save(self, doc: FeatureExperimentDocument) -> None:
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


@dataclass
class PPIIndexRepository:
    """
    Read/bulk-write ProteinProteinDocument to a specific *concrete* ES index.
    Use with your PPI CSV flow. Accepts raw bulk actions or DSL docs.
    """

    concrete_index: str
    client: Optional[Elasticsearch] = None

    def _conn(self) -> Elasticsearch:
        return self.client or connections.get_connection()

    def ensure_index(self) -> None:
        es = self._conn()
        # If concrete index exists, add v4 fields and leave existing field types alone.
        if es.indices.exists(index=self.concrete_index):
            self._ensure_v4_mapping(es)
            return
        # If it's an alias, DO NOT create a new index. Just use the alias target(s).
        if es.indices.exists_alias(name=self.concrete_index):
            self._ensure_v4_mapping(es)
            return
        ProteinProteinDocument.init(index=self.concrete_index, using=es)

    def _ensure_v4_mapping(self, es: Elasticsearch) -> None:
        """Add PPI v4 properties. Warn when consensus_score cannot store full precision."""
        try:
            es.indices.put_mapping(index=self.concrete_index, properties=PPI_V4_MAPPING_PROPERTIES)
        except Exception as exc:
            logger.warning(
                "[ppi] could not add v4 field mapping on %s: %s", self.concrete_index, exc
            )
            return

        score_type = _mapped_field_type(es, self.concrete_index, "consensus_score")
        if score_type and score_type != "double":
            logger.warning(
                "[ppi] %s maps consensus_score as %s. Recreate the PPI index before "
                "loading v4 so consensus and category scores keep full TSV precision.",
                self.concrete_index,
                score_type,
            )

    def get(self, pair_id: str) -> Optional[ProteinProteinDocument]:
        try:
            return ProteinProteinDocument.get(
                id=pair_id, index=self.concrete_index, using=self._conn(), ignore=404
            )
        except NotFoundError:
            return None

    def save(self, doc: ProteinProteinDocument) -> None:
        # make sure index/mapping exists
        self.ensure_index()
        doc.save(index=self.concrete_index, using=self._conn())

    def bulk_index(
        self,
        actions: Iterable[Dict[str, Any]],
        *,
        chunk_size: int = 2000,
        refresh: Optional[str | bool] = None,  # e.g. "wait_for"
        raise_on_error: bool = False,
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Bulk index raw actions. Automatically sets _index if missing and ensures mapping.
        Returns (success_count, failures).
        """
        self.ensure_index()

        # Materialize and enforce _index/_op_type for idempotent upserts
        acts: List[Dict[str, Any]] = []
        for a in actions:
            a = dict(a)
            a.setdefault("_index", self.concrete_index)
            a.setdefault("_op_type", "index")
            acts.append(a)

        if not acts:
            return 0, []

        try:
            success, failures = es_bulk(
                self._conn(),
                acts,
                chunk_size=chunk_size,
                raise_on_error=raise_on_error,
                refresh=refresh,
            )
            if failures:
                # keep your lightweight logging style
                print(f"[es_repo] PPI bulk failures: {len(failures)} (first 3 shown)")
                for f in failures[:3]:
                    print(f"  -> {f}")
            return success, failures
        except BulkIndexError as e:
            errs = getattr(e, "errors", [])
            print(f"[es_repo] PPI BulkIndexError with {len(errs)} errors (first 3 shown)")
            for f in errs[:3]:
                print(f"  -> {f}")
            return 0, errs


def _mapped_field_type(es: Elasticsearch, index: str, field: str) -> Optional[str]:
    try:
        mapping = es.indices.get_mapping(index=index)
    except Exception:
        return None
    for body in mapping.values():
        spec = body.get("mappings", {}).get("properties", {}).get(field)
        if isinstance(spec, dict):
            return spec.get("type")
    return None


@dataclass
class OperonIndexRepository:
    concrete_index: str

    def get(self, doc_id: str) -> Optional[OperonDocument]:
        try:
            return OperonDocument.get(id=doc_id, index=self.concrete_index, ignore=404)
        except NotFoundError:
            return None

    def save(self, doc: OperonDocument) -> None:
        doc.save(index=self.concrete_index)


@dataclass
class OrthologIndexRepository:
    concrete_index: str

    def get(self, pair_id: str) -> Optional[OrthologDocument]:
        try:
            return OrthologDocument.get(id=pair_id, index=self.concrete_index, ignore=404)
        except NotFoundError:
            return None

    def save(self, doc: OrthologDocument) -> None:
        doc.save(index=self.concrete_index)


@dataclass
class GeneFitnessCorrelationIndexRepository:
    """
    Read/bulk-write GeneFitnessCorrelationDocument to a specific *concrete* ES index.
    Similar to PPIIndexRepository but for gene fitness correlations.
    """

    concrete_index: str
    client: Optional[Elasticsearch] = None

    def _conn(self) -> Elasticsearch:
        return self.client or connections.get_connection()

    def ensure_index(self) -> None:
        es = self._conn()
        if es.indices.exists(index=self.concrete_index):
            return
        if es.indices.exists_alias(name=self.concrete_index):
            return

    def get(self, pair_id: str) -> Optional[GeneFitnessCorrelationDocument]:
        try:
            return GeneFitnessCorrelationDocument.get(
                id=pair_id, index=self.concrete_index, using=self._conn(), ignore=404
            )
        except NotFoundError:
            return None

    def save(self, doc: GeneFitnessCorrelationDocument) -> None:
        self.ensure_index()
        doc.save(index=self.concrete_index, using=self._conn())

    def bulk_index(
        self,
        actions: Iterable[Dict[str, Any]],
        *,
        chunk_size: int = 2000,
        refresh: Optional[str | bool] = None,
        raise_on_error: bool = False,
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Bulk index raw actions for gene fitness correlations.
        Returns (success_count, failures).
        """
        self.ensure_index()

        acts: List[Dict[str, Any]] = []
        for a in actions:
            a = dict(a)
            a.setdefault("_index", self.concrete_index)
            a.setdefault("_op_type", "index")
            acts.append(a)

        if not acts:
            return 0, []

        try:
            success, failures = es_bulk(
                self._conn(),
                acts,
                chunk_size=chunk_size,
                raise_on_error=raise_on_error,
                refresh=refresh,
            )
            if failures:
                print(
                    f"[es_repo] GeneFitnessCorrelation bulk failures: {len(failures)} (first 3 shown)"
                )
                for f in failures[:3]:
                    print(f"  -> {f}")
            return success, failures
        except BulkIndexError as e:
            errs = getattr(e, "errors", [])
            print(
                f"[es_repo] GeneFitnessCorrelation BulkIndexError with {len(errs)} errors (first 3 shown)"
            )
            for f in errs[:3]:
                print(f"  -> {f}")
            return 0, errs


# -----------------------------
# Bulk utilities
# -----------------------------


def _partition_bulk_failures(failures: List[Dict[str, Any]] | None):
    missing: List[Dict[str, Any]] = []
    real: List[Dict[str, Any]] = []
    for item in failures or []:
        body = item.get("update") or item.get("index") or item.get("create") or item.get("delete")
        if not isinstance(body, dict):
            real.append(item)
            continue
        err = body.get("error") or {}
        err_type = err.get("type") if isinstance(err, dict) else None
        if body.get("status") == 404 or err_type == "document_missing_exception":
            missing.append(item)
        else:
            real.append(item)
    return missing, real


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
        missing, real = _partition_bulk_failures(failures)
        if missing:
            print(
                f"[es_repo] Skipped {len(missing)} update(s) for documents that are not in the "
                f"feature index (expected for fitness IG rows whose neighbors are not genes)."
            )
        if real:
            print(f"[es_repo] Bulk failures: {len(real)} (first 3 shown)")
            for f in real[:3]:
                print(f"  -> {f}")
        return success, failures
    except BulkIndexError as e:
        errs = getattr(e, "errors", [])
        missing, real = _partition_bulk_failures(errs)
        if missing:
            print(f"[es_repo] Skipped {len(missing)} update(s) for missing feature documents.")
        if real:
            print(f"[es_repo] BulkIndexError with {len(real)} errors (first 3 shown)")
            for f in real[:3]:
                print(f"  -> {f}")
        return 0, errs


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
if (params.containsKey('ig_locus_tag_a') && params.ig_locus_tag_a != null) {
  ctx._source.ig_locus_tag_a = params.ig_locus_tag_a;
  ctx._source.ig_locus_tag_b = params.ig_locus_tag_b;
  ctx._source.flanking_locus_tags = [params.ig_locus_tag_a, params.ig_locus_tag_b];
}
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

SCRIPT_UPSERT_ESSENTIALITY = """
if (ctx._source == null) { ctx._source = [:]; }

// 1) Merge base fields (only if missing to avoid clobbering)
if (params.base != null) {
  for (entry in params.base.entrySet()) {
    def k = entry.getKey();
    def v = entry.getValue();
    if (ctx._source[k] == null) { ctx._source[k] = v; }
  }
}

// 2) Append to nested array with de-dup
def field = params.field;
def ent   = params.entry;
def keys  = params.keys;
if (field != null && ent != null) {
  if (ctx._source[field] == null) { ctx._source[field] = []; }
  boolean exists = false;
  if (keys != null) {
    for (item in ctx._source[field]) {
      boolean same = true;
      for (k in keys) {
        if (item[k] != ent[k]) { same = false; break; }
      }
      if (same) { exists = true; break; }
    }
  }
  if (!exists) { ctx._source[field].add(ent); }
  
  // Set has_essentiality flag when essentiality data is added
  ctx._source.has_essentiality = true;
}

// 3) Set legacy flat essentiality for backward compatibility (first available call)
if (params.legacy != null && ctx._source.essentiality == null) {
  ctx._source.essentiality = params.legacy;
}
"""
