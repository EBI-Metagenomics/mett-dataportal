from typing import Any, Dict

from dataportal.ingest.es_repo import bulk_exec
from dataportal.ingest.feature.flows.base import Flow
from dataportal.ingest.utils import chunks_from_table


class Proteomics(Flow):
    """
    Upserts proteomics evidence from TSV files.

    Expected columns (tab-separated):
      Protein, Coverage, Unique Peptides, Unique Intensity, Proteomics Evidence (Y/N)
    """

    def __init__(self, index_name: str = "feature_index"):
        super().__init__(index_name=index_name)

    def run(self, tsv_or_csv_path: str, chunksize: int = 10_000) -> None:
        actions: list[Dict[str, Any]] = []
        for chunk in chunks_from_table(tsv_or_csv_path, chunksize=chunksize):
            for rec in chunk.to_dict(orient="records"):
                fid = self._str(rec.get("Protein"))
                if not fid: continue
                coverage = self._to_float(rec.get("Coverage"))
                unique_peptides = self._to_int(rec.get("Unique Peptides"))
                unique_intensity = self._to_float(rec.get("Unique Intensity"))
                evidence = self._str(rec.get("Proteomics Evidence")).lower().startswith("y")
                entry = {
                    "coverage": coverage,
                    "unique_peptides": unique_peptides,
                    "unique_intensity": unique_intensity,
                    "evidence": evidence,
                }
                actions.append({
                    "_op_type": "update",
                    "_index": self.index,
                    "_id": fid,
                    "script": {
                        "source": """
    if (ctx._source.proteomics == null) { ctx._source.proteomics = []; }
    ctx._source.proteomics.add(params.entry);
    ctx._source.has_proteomics = true;
    """,
                        "params": {"entry": entry},
                    },
                    "upsert": {
                        "feature_id": fid,
                        "feature_type": "gene",
                        "proteomics": [entry],
                        "has_proteomics": True,
                    },
                    "scripted_upsert": True,
                })
                if len(actions) >= 500:
                    bulk_exec(actions);
                    actions.clear()
        if actions:
            bulk_exec(actions);
            actions.clear()

    # ---- helpers ----
    @staticmethod
    def _str(v: Any) -> str:
        return "" if v is None else str(v).strip()

    @staticmethod
    def _to_int(v: Any, default: int = 0) -> int:
        try:
            if v in (None, "", "nan", "NaN"): return default
            return int(float(v))
        except Exception:
            return default

    @staticmethod
    def _to_float(v: Any, default: float = 0.0) -> float:
        try:
            if v in (None, "", "nan", "NaN"): return default
            return float(v)
        except Exception:
            return default
