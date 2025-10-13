from typing import Any, Dict
import pandas as pd

from dataportal.ingest.constants import VALID_ESSENTIALITY
from dataportal.ingest.es_repo import bulk_exec, SCRIPT_UPSERT_ESSENTIALITY
from dataportal.ingest.feature.flows.base import Flow
from dataportal.ingest.utils import (
    canonical_ig_id_from_neighbors, 
    chunks_from_table,
    parse_ig_neighbors,
    extract_isolate_from_locus_tag,
    get_species_metadata_from_isolate,
)


class Essentiality(Flow):
    """
    Upserts essentiality for genes and creates IG documents on the fly.

    Expected columns:
      locus_tag, element, TAs_in_locus, TAs_hit, essentiality_call, experimental_condition
      (For IG rows, 'locus_tag' is the legacy label "IG-between-LEFT-and-RIGHT")
    """

    def __init__(self, index_name: str = "feature_index"):
        super().__init__(index_name=index_name)
        self._species_cache = {}  # Cache for species lookups

    def run(self, csv_path: str, chunksize: int = 10_000) -> None:
        actions: list[Dict[str, Any]] = []

        for chunk in chunks_from_table(csv_path, chunksize=chunksize):
            for rec in chunk.to_dict(orient="records"):
                raw_id = self._str(rec.get("locus_tag"))
                if not raw_id:
                    continue

                element = (self._str(rec.get("element")) or "").lower() or None
                call = (self._str(rec.get("essentiality_call")) or "").lower() or None
                cond = self._str(rec.get("experimental_condition")) or None
                tas_in_locus = self._to_int(rec.get("TAs_in_locus"), default=0)
                tas_hit = self._to_float(rec.get("TAs_hit"), default=0.0)

                # feature_id: genes keep locus_tag, IGs become IG:<LEFT>__<RIGHT>
                if element == "gene":
                    fid = raw_id
                else:
                    left, right = parse_ig_neighbors(raw_id)  # parse legacy text
                    fid = canonical_ig_id_from_neighbors(left, right) or raw_id

                # Base fields (merged by script only if missing)
                base = {
                    "feature_id": fid,
                    "feature_type": "gene" if element == "gene" else "IG",
                    "element": element or ("intergenic" if raw_id.startswith("IG-between-") else None),
                    "has_essentiality": True,  # Set flag when essentiality data is available
                }
                if base["feature_type"] == "IG":
                    left, right = parse_ig_neighbors(raw_id)
                    if left and right:
                        # Extract and add species metadata for IG features
                        isolate_name = extract_isolate_from_locus_tag(left)
                        if isolate_name:
                            species_metadata = get_species_metadata_from_isolate(isolate_name, self._species_cache)
                            base.update(species_metadata)
                        
                        base.update({
                            "ig_locus_tag_a": left,
                            "ig_locus_tag_b": right,
                            "ig_locus_tag_a_kw": left,
                            "ig_locus_tag_b_kw": right,
                            "legacy_ig_label": raw_id,
                        })

                # Complete nested entry (include element)
                entry = {
                    "experimental_condition": cond,
                    "TAs_in_locus": tas_in_locus,
                    "TAs_hit": tas_hit,
                    "essentiality_call": call,
                    "element": element,
                }

                actions.append({
                    "_op_type": "update",
                    "_index": self.index,
                    "_id": fid,
                    "script": {
                        "source": SCRIPT_UPSERT_ESSENTIALITY,
                        "params": {
                            "base": base,
                            "field": "essentiality_data",
                            "entry": entry,
                            "keys": ["experimental_condition", "TAs_in_locus", "TAs_hit", "essentiality_call", "element"],
                            "legacy": (call if call in VALID_ESSENTIALITY else None),
                        },
                    },
                    "upsert": {},
                    "scripted_upsert": True,
                })

                if len(actions) >= 500:
                    bulk_exec(actions); actions.clear()

            if actions:
                bulk_exec(actions); actions.clear()

    # ---------- helpers ----------
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
