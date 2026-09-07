from abc import ABC, abstractmethod

from dataportal.ingest.constants import BATCH_SIZE
from dataportal.ingest.es_repo import bulk_exec
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

    def add_feature_flag(self, actions: list, fid: str, flag_field: str) -> None:
        """Denormalize has_* flags onto the current feature index (gene search/facets)."""
        if not self.feature_flag_index or not flag_field or not fid:
            return
        actions.append(
            {
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
        )

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
