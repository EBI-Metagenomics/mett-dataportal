import pandas as pd

from dataportal.ingest.es_repo import bulk_exec, SCRIPT_APPEND_AND_SET_FLAG
from dataportal.ingest.feature.flows.base import Flow
from dataportal.ingest.utils import pick
from dataportal.models import FeatureDocument


class Proteomics(Flow):
    """
    CSV columns (examples from your sample):
      Protein, Coverage, Unique Peptides, Unique Intensity, Proteomics Evidence(Y/N)
    """

    def __init__(self, index_name: str = "feature_index"):
        super().__init__(index_name=index_name)

    def run(self, csv_path):
        actions = []
        for chunk in pd.read_csv(csv_path, chunksize=10000):
            for rec in chunk.to_dict(orient="records"):
                fid = str(pick(rec, "Protein", "locus_tag", default="") or "").strip()
                if not fid:
                    continue
                coverage = rec.get("Coverage")
                upep = pick(rec, "Unique Peptides", "Unique_Peptides")
                uint = pick(rec, "Unique Intensity", "Unique_Intensity")
                evid_raw = pick(rec, "Proteomics Evidence", "Proteomics_Evidence", default="N")
                evidence = str(evid_raw).strip().upper() in ("Y", "YES", "TRUE", "1")

                entry = {
                    "coverage": float(coverage) if coverage not in (None, "") else None,
                    "unique_peptides": int(upep) if upep not in (None, "") else None,
                    "unique_intensity": float(uint) if uint not in (None, "") else None,
                    "evidence": evidence,
                }
                actions.append({
                    "_op_type": "update",
                    "_index": self.index,
                    "_id": fid,
                    "script": {
                        "source": SCRIPT_APPEND_AND_SET_FLAG,
                        "params": {"field": "proteomics", "entry": entry, "flag_field": "has_proteomics"},
                    },
                    "upsert": {"feature_id": fid, "feature_type": "gene", "proteomics": [entry],
                               "has_proteomics": True},
                })
                if len(actions) >= 500:
                    bulk_exec(actions);
                    actions.clear()
        if actions:
            bulk_exec(actions)
