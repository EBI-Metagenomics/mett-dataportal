import pandas as pd

from dataportal.ingest.es_repo import bulk_exec, SCRIPT_APPEND_NESTED_DEDUP_BY_KEYS, SCRIPT_APPEND_AND_SET_FLAG
from dataportal.ingest.feature.flows.base import Flow
from dataportal.ingest.utils import pick
from dataportal.models import FeatureDocument


class ProteinCompound(Flow):
    """
    CSV columns from your sample:
      index (locus_tag), condition (compound), thermal_stability_score, adj.pValue, hit_calling(0/1)
    """

    def __init__(self, index_name: str = "feature_index"):
        super().__init__(index_name=index_name)

    def run(self, csv_path):
        actions = []
        for chunk in pd.read_csv(csv_path, chunksize=10000):
            for rec in chunk.to_dict(orient="records"):
                fid = str(pick(rec, "index", "locus_tag", default="") or "").strip()
                if not fid:
                    continue
                comp = pick(rec, "condition", "compound")
                tss = rec.get("thermal_stability_score")
                fdr = pick(rec, "adj.pValue", "adj_pValue", "fdr")
                hit = rec.get("hit_calling")
                try:
                    hit_bool = bool(int(hit))
                except Exception:
                    hit_bool = str(hit).strip() in ("True", "true", "Y", "1")

                entry = {
                    "compound": str(comp).strip() if comp else None,
                    "ttp_score": float(tss) if tss not in (None, "") else None,
                    "fdr": float(fdr) if fdr not in (None, "") else None,
                    "hit_calling": hit_bool,
                    "experimental_condition": None,
                }

                # dedup by compound name
                actions.append({
                    "_op_type": "update",
                    "_index": self.index,
                    "_id": fid,
                    "script": {
                        "source": SCRIPT_APPEND_NESTED_DEDUP_BY_KEYS + "\n" + SCRIPT_APPEND_AND_SET_FLAG,
                        "params": {"field": "protein_compound", "entry": entry, "keys": ["compound"],
                                   "flag_field": "has_proteomics"},
                    },
                    "upsert": {"feature_id": fid, "feature_type": "gene", "protein_compound": [entry],
                               "has_proteomics": True},
                })

                if len(actions) >= 500:
                    bulk_exec(actions);
                    actions.clear()
        if actions:
            bulk_exec(actions)
