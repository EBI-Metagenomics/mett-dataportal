from abc import ABC, abstractmethod

from dataportal.ingest.constants import BATCH_SIZE
from dataportal.ingest.es_repo import bulk_exec
from dataportal.ingest.utils import (
    extract_isolate_from_locus_tag,
    get_species_metadata_from_isolate,
    ig_neighbor_fields,
)
from dataportal.utils.constants import INDEX_FEATURES


class Flow(ABC):
    def __init__(
        self,
        index_name: str = INDEX_FEATURES,
        feature_flag_index: str | None = None,
    ):
        self.index = index_name
        self.feature_flag_index = feature_flag_index
        self.buffer = []
        self._species_cache = {}

    def add_feature_flag(self, actions: list, fid: str, flag_field: str) -> None:
        """Set has_* on the feature index. Interval IGs (IG:A__B) are upserted so they
        remain searchable; GFF only writes genes, essentiality/fitness create IGs.
        """
        if not self.feature_flag_index or not flag_field or not fid:
            return
        fid = str(fid)
        action = {
            "_op_type": "update",
            "_index": self.feature_flag_index,
            "_id": fid,
            "script": {
                "source": (
                    "if (ctx._source == null) { ctx._source = [:]; } "
                    "ctx._source[params.flag] = true;"
                ),
                "lang": "painless",
                "params": {"flag": flag_field},
            },
        }
        if fid.startswith("IG:"):
            upsert = {
                "feature_id": fid,
                "feature_type": "IG",
                "element": "intergenic",
                "locus_tag": fid,
                flag_field: True,
            }
            rest = fid[3:]
            if "__" in rest:
                left, right = rest.split("__", 1)
                upsert.update(ig_neighbor_fields(fid, left, right))
                isolate = extract_isolate_from_locus_tag(left)
                if isolate:
                    upsert.update(get_species_metadata_from_isolate(isolate, self._species_cache))
            action["upsert"] = upsert
            action["scripted_upsert"] = True
        actions.append(action)

    @abstractmethod
    def run(self, *args, **kwargs): ...

    def add(self, action):
        self.buffer.append(action)
        if len(self.buffer) >= BATCH_SIZE:
            self.flush()

    def flush(self):
        if not self.buffer:
            return
        bulk_exec(self.buffer)
        self.buffer.clear()
