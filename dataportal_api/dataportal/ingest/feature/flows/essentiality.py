from typing import Any, Dict

import pandas as pd

from dataportal.ingest.constants import VALID_ESSENTIALITY
from dataportal.ingest.es_repo import bulk_exec, SCRIPT_APPEND_NESTED
from dataportal.ingest.feature.flows.base import Flow
from dataportal.ingest.feature.parsing import parse_ig_neighbors


class Essentiality(Flow):
    """
    Upserts essentiality for genes and creates IG documents on the fly.

    CSV expected columns (case-sensitive examples):
      - locus_tag
      - element                  (gene, intergenic, ncRNA, tRNA, ...)
      - TAs_in_locus             (int)
      - TAs_hit                  (float 0..1)
      - essentiality_call        (essential, not_essential, essential_solid, essential_liquid, not_classified, unclear)
      - experimental_condition   (string)

    Robustness:
      - Silently skips rows without a locus_tag.
      - Accepts floats/ints/strings for numeric fields and coerces them safely.
      - If 'element' looks like IG (or locus_tag starts with IG-between-), adds ig_locus_tag_a/b (+ keyword mirrors).
    """

    def __init__(self, index_name: str = "feature_index"):
        super().__init__(index_name=index_name)

    def run(self, csv_path: str, chunksize: int = 10_000) -> None:
        actions: list[Dict[str, Any]] = []

        for chunk in pd.read_csv(csv_path, chunksize=chunksize):
            for rec in chunk.to_dict(orient="records"):
                fid = self._str(rec.get("locus_tag"))
                if not fid:
                    continue

                element = self._str(rec.get("element")).lower() or None
                call = self._str(rec.get("essentiality_call")).lower() or None
                cond = self._str(rec.get("experimental_condition")) or None
                tas_in_locus = self._to_int(rec.get("TAs_in_locus"), default=0)
                tas_hit = self._to_float(rec.get("TAs_hit"), default=0.0)

                # Upsert base doc (created if not present)
                base = {
                    "feature_id": fid,
                    "feature_type": "gene" if element == "gene" else "IG",
                    "element": element or ("intergenic" if fid.startswith("IG-between-") else None),
                    "essentiality": call if call in VALID_ESSENTIALITY else None,
                }

                # Populate IG neighbor fields when applicable
                if base["feature_type"] == "IG":
                    a, b = parse_ig_neighbors(fid)
                    if a and b:
                        base.update({
                            "ig_locus_tag_a": a,
                            "ig_locus_tag_b": b,
                            "ig_locus_tag_a_kw": a,  # exact-match mirrors
                            "ig_locus_tag_b_kw": b,
                        })

                entry = {
                    "experimental_condition": cond,
                    "TAs_in_locus": tas_in_locus,
                    "TAs_hit": tas_hit,
                    "essentiality_call": call,
                }

                actions.append({
                    "_op_type": "update",
                    "_index": self.index,
                    "_id": fid,
                    "script": {
                        "source": SCRIPT_APPEND_NESTED,
                        "params": {"field": "essentiality_data", "entry": entry},
                    },
                    "upsert": base,
                })

                if len(actions) >= 500:
                    bulk_exec(actions)
                    actions.clear()

            if actions:
                bulk_exec(actions)
                actions.clear()

    # -----------------------------
    # Small coercion helpers
    # -----------------------------
    @staticmethod
    def _str(v: Any) -> str:
        if v is None:
            return ""
        s = str(v).strip()
        return "" if s.lower() in ("nan", "none") else s

    @staticmethod
    def _to_int(v: Any, default: int = 0) -> int:
        try:
            if v in (None, "", "nan", "NaN"):
                return default
            return int(float(v))
        except Exception:
            return default

    @staticmethod
    def _to_float(v: Any, default: float = 0.0) -> float:
        try:
            if v in (None, "", "nan", "NaN"):
                return default
            return float(v)
        except Exception:
            return default
