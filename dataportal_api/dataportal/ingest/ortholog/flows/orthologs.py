# ingest/ortholog/flows/orthologs.py
from __future__ import annotations
from typing import Any, Dict, List
from dataportal.ingest.feature.flows.base import Flow
from dataportal.ingest.es_repo import bulk_exec
from dataportal.ingest.utils import chunks_from_table, canonical_pair_id


def _keys_map(cols) -> Dict[str, str]:
    return {str(c).lower().strip(): c for c in cols}


def _get(rec: Dict[str, Any], km: Dict[str, str], *names, default=None):
    for n in names:
        k = km.get(str(n).lower().strip())
        if k is not None:
            return rec.get(k, default)
    return default


class Orthologs(Flow):
    """
    Builds order-insensitive pair docs:
      pair_id = "ORTHO:<A>__<B>"

    Doc schema (no painless):
      {
        "pair_id": "...",
        "doc_type": "pair",
        "gene_a": "...",
        "gene_b": "...",
        "orthology_type": "1:1|1:many|many:1|many:many|...",
        "oma_group": "...|None",
        "members": ["A","B"]
      }
    """

    def __init__(self, index_name: str = "ortholog_index"):
        super().__init__(index_name=index_name)
        self._docs: Dict[str, Dict[str, Any]] = {}

    def run(self, path: str, chunksize: int = 5_000) -> None:
        rows = 0
        for chunk in chunks_from_table(path, chunksize=chunksize):
            km = _keys_map(chunk.columns)
            for rec in chunk.to_dict(orient="records"):
                rows += 1
                a = _get(rec, km, "Protein 1", "protein 1", "gene_a_locus_tag", "genea", "gene_a", "Gene 1")
                b = _get(rec, km, "Protein 2", "protein 2", "gene_b_locus_tag", "geneb", "gene_b", "Gene 2")
                if not a or not b:
                    continue
                a, b = str(a).strip(), str(b).strip()

                pid = canonical_pair_id(a, b, prefix="ORTHO")
                otype = _get(rec, km, "Orthology type", "orthology type", "orthology_type")
                oma = _get(rec, km, "OMA group", "oma group", "oma_group")

                doc = self._docs.get(pid)
                if not doc:
                    doc = {
                        "pair_id": pid,
                        "doc_type": "pair",
                        "gene_a": a,
                        "gene_b": b,
                        "orthology_type": None,
                        "oma_group": None,
                        "members": [a, b],
                    }
                    self._docs[pid] = doc

                # set if provided; do not override with empty values
                if otype not in (None, "", "nan", "NaN"):
                    doc["orthology_type"] = str(otype).strip()
                if oma not in (None, "", "nan", "NaN"):
                    doc["oma_group"] = str(oma).strip()

        print(f"[orthologs] processed rows from {path}: {rows}")

    def flush(self) -> None:
        if not self._docs:
            return
        actions: List[Dict[str, Any]] = []
        for pid, src in self._docs.items():
            actions.append({
                "_op_type": "index",  # overwrite ok for fresh import
                "_index": self.index,
                "_id": pid,
                "_source": src,
            })
            if len(actions) >= 1000:
                bulk_exec(actions); actions.clear()
        if actions:
            bulk_exec(actions); actions.clear()
        print(f"[orthologs] indexed docs: {len(self._docs)}")
        # self._docs.clear()
