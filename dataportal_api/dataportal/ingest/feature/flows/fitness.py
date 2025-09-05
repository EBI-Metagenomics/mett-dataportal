import pandas as pd
from dataportal.ingest.feature.flows.base import Flow
from dataportal.ingest.es_repo import bulk_exec, SCRIPT_APPEND_AND_SET_FLAG
from dataportal.models import FeatureDocument
from dataportal.ingest.utils import pick



class Fitness(Flow):
    """
    CSV flexible columns:
      - prefer: locus_tag, experimental_condition, media, contrast, lfc, fdr
      - fallback: 'Name' for locus_tag, 'LFC'/'FDR' for values
    """

    def __init__(self, index_name: str = "feature_index"):
        super().__init__(index_name=index_name)

    def run(self, csv_path):
        actions = []
        for chunk in pd.read_csv(csv_path, chunksize=10000):
            for rec in chunk.to_dict(orient="records"):
                fid = str(pick(rec, "locus_tag", "Name", default="") or "").strip()
                if not fid:
                    continue
                entry = {
                    "experimental_condition": pick(rec, "experimental_condition", "contrast"),
                    "media": rec.get("media"),
                    "contrast": rec.get("contrast"),
                    "lfc": float(rec.get("lfc", rec.get("LFC"))) if pick(rec, "lfc", "LFC") is not None else None,
                    "fdr": float(rec.get("fdr", rec.get("FDR"))) if pick(rec, "fdr", "FDR") is not None else None,
                }
                actions.append({
                    "_op_type": "update",
                    "_index": self.index,
                    "_id": fid,
                    "script": {
                        "source": SCRIPT_APPEND_AND_SET_FLAG,
                        "params": {"field": "fitness", "entry": entry, "flag_field": "has_fitness"},
                    },
                    "upsert": {"feature_id": fid, "feature_type": "gene", "fitness": [entry], "has_fitness": True},
                })
                if len(actions) >= 500:
                    bulk_exec(actions); actions.clear()
        if actions:
            bulk_exec(actions)
