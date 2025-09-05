import pandas as pd

from dataportal.ingest.es_repo import bulk_exec, SCRIPT_APPEND_AND_SET_FLAG
from dataportal.ingest.feature.flows.base import Flow
from dataportal.ingest.utils import pick
from dataportal.models import FeatureDocument


class MutantGrowth(Flow):
    """
    CSV columns from your sample (varies):
      index or gene_locus_tag, media, mutant_replicate, TAs_hit_(0-1), doubling_rate[h]
    Uses dict iteration to avoid itertuples name-mangling.
    """

    def __init__(self, index_name: str = "feature_index"):
        super().__init__(index_name=index_name)

    def run(self, csv_path):
        actions = []
        for chunk in pd.read_csv(csv_path, chunksize=10000):
            for rec in chunk.to_dict(orient="records"):
                fid = str(pick(rec, "index", "gene_locus_tag", "locus_tag", default="") or "").strip()
                if not fid:
                    continue
                entry = {
                    "media": pick(rec, "media", "media_id"),
                    "experimental_condition": rec.get("experimental_condition"),
                    "replicate": int(pick(rec, "mutant_replicate", "replicate", default=1) or 1),
                    "tas_hit": float(pick(rec, "TAs_hit_(0-1)", "tas_hit", default=0) or 0),
                    "doubling_rate_h": float(pick(rec, "doubling_rate[h]", "doubling_rate_h", default=0) or 0),
                }
                actions.append({
                    "_op_type": "update",
                    "_index": self.index,
                    "_id": fid,
                    "script": {
                        "source": SCRIPT_APPEND_AND_SET_FLAG,
                        "params": {"field": "mutant_growth", "entry": entry, "flag_field": "has_mutant_growth"},
                    },
                    "upsert": {"feature_id": fid, "feature_type": "gene", "mutant_growth": [entry],
                               "has_mutant_growth": True},
                })
                if len(actions) >= 500:
                    bulk_exec(actions);
                    actions.clear()
        if actions:
            bulk_exec(actions)
