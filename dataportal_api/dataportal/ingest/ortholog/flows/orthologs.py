
from __future__ import annotations

import gc
from typing import Any, Dict, List
from dataportal.ingest.feature.flows.base import Flow
from dataportal.ingest.es_repo import bulk_exec
from dataportal.ingest.utils import canonical_pair_id

import pandas as pd


def _keys_map(cols) -> Dict[str, str]:
    return {str(c).lower().strip(): c for c in cols}


def _get(rec: Dict[str, Any], km: Dict[str, str], *names, default=None):
    for n in names:
        k = km.get(str(n).lower().strip())
        if k is not None:
            return rec.get(k, default)
    return default


def _split_locus_and_desc(cell: Any) -> tuple[str, str]:
    """
    Split "BU_61_00001 Chromosomal ..." -> ("BU_61_00001", "Chromosomal ...").
    If no space is found, returns (cell, "").
    """
    if cell is None:
        return "", ""
    s = str(cell).strip()
    if not s:
        return "", ""
    if " " in s:
        locus, desc = s.split(" ", 1)
        return locus.strip(), desc.strip()
    return s, ""


class Orthologs(Flow):
    """
    Builds order-insensitive pair docs:
      pair_id = "<A>__<B>"

    Doc schema (no painless):
      {
        "pair_id": "...",
        "doc_type": "pair",
        "gene_a": "...",   # locus/protein id ONLY (description trimmed)
        "gene_b": "...",
        "orthology_type": "...",
        "oma_group": "...|None",
        "members": ["A","B"],
        # Optional:
        "desc_a": "...",
        "desc_b": "..."
      }
    """

    def __init__(self, index_name: str = "ortholog_index"):
        super().__init__(index_name=index_name)
        self._docs: Dict[str, Dict[str, Any]] = {}

    def _iter_chunks(self, path: str, chunksize: int):
        """
        Robust TSV reader:
        - Treats file as tab-separated
        - Ignores lines starting with '#'
        - File has NO real header row after comments, so we provide names
        - Only first 6 columns are used; extra columns are skipped
        """
        expected_cols = [
            "seq_a",
            "seq_b",
            "Protein 1",  # "PROTEIN_ID Description..."
            "Protein 2",
            "Orthology type",
            "OMA group",
        ]

        return pd.read_csv(
            path,
            sep="\t",
            comment="#",
            header=None,  # there is no real header after comments
            names=expected_cols,  # consistent names for our _get()
            usecols=list(range(6)),  # guard against ragged rows
            dtype=str,  # keep raw strings
            chunksize=chunksize,
            engine="python",  # more forgiving with comments/mixed rows
            on_bad_lines="skip",
            na_filter=False,
            memory_map=False,
        )

    def run(self, path: str, chunksize: int = 100_000, flush_every: int = 200_000) -> None:
        rows = 0
        seen_since_flush = 0

        try:
            for chunk in self._iter_chunks(path, chunksize=chunksize):
                km = _keys_map(chunk.columns)

                for rec in chunk.to_dict(orient="records"):
                    rows += 1

                    raw_a = _get(
                        rec, km,
                        "Protein 1", "protein 1", "Gene 1", "gene 1",
                        "gene_a_locus_tag", "genea", "gene_a"
                    )
                    raw_b = _get(
                        rec, km,
                        "Protein 2", "protein 2", "Gene 2", "gene 2",
                        "gene_b_locus_tag", "geneb", "gene_b"
                    )
                    if not raw_a or not raw_b:
                        continue

                    # Trim description text, keep only IDs in gene_a/gene_b
                    a_id, a_desc = _split_locus_and_desc(raw_a)
                    b_id, b_desc = _split_locus_and_desc(raw_b)
                    if not a_id or not b_id:
                        continue

                    pid = canonical_pair_id(a_id, b_id)

                    otype = _get(rec, km, "Orthology type", "orthology type", "orthology_type")
                    oma = _get(rec, km, "OMA group", "oma group", "oma_group", "OMA group (if any)")

                    doc = self._docs.get(pid)
                    if not doc:
                        doc = {
                            "pair_id": pid,
                            "doc_type": "pair",
                            "gene_a": a_id,
                            "gene_b": b_id,
                            "orthology_type": None,
                            "oma_group": None,
                            "members": [a_id, b_id],
                        }
                        if a_desc:
                            doc["desc_a"] = a_desc
                        if b_desc:
                            doc["desc_b"] = b_desc

                        self._docs[pid] = doc
                        seen_since_flush += 1

                    # set if provided; do not override with empty values
                    if otype not in (None, "", "nan", "NaN"):
                        doc["orthology_type"] = str(otype).strip()
                    if oma not in (None, "", "nan", "NaN"):
                        doc["oma_group"] = str(oma).strip()

                    # Periodic flush to cap memory on huge files
                    if flush_every and seen_since_flush >= flush_every:
                        self._flush_partial()
                        seen_since_flush = 0

                # drop chunk ASAP and GC
                del km
                del chunk
                gc.collect()

        finally:
            # IMPORTANT: flush any stragglers at the end of THIS FILE
            if self._docs:
                self._flush_partial()

        print(f"[orthologs] processed rows from {path}: {rows}")

    def _flush_partial(self) -> None:
        if not self._docs:
            return
        actions: List[Dict[str, Any]] = []
        # keep batch small (1000) to avoid big lists in RAM
        for pid, src in self._docs.items():
            actions.append({
                "_op_type": "index",
                "_index": self.index,
                "_id": pid,
                "_source": src,
            })
            if len(actions) >= 1000:
                bulk_exec(actions)
                actions.clear()
        if actions:
            bulk_exec(actions)
        print(f"[orthologs] partial index flush: {len(self._docs)} docs")
        # FREE the cache
        self._docs.clear()

    def flush(self) -> None:
        # stays as a safety net; usually run() will have flushed already
        if not self._docs:
            return
        actions: List[Dict[str, Any]] = []
        for pid, src in self._docs.items():
            actions.append({
                "_op_type": "index",
                "_index": self.index,
                "_id": pid,
                "_source": src,
            })
            if len(actions) >= 1000:
                bulk_exec(actions);
                actions.clear()
        if actions:
            bulk_exec(actions);
            actions.clear()
        print(f"[orthologs] indexed docs: {len(self._docs)}")
        self._docs.clear()
