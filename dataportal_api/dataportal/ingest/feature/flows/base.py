from abc import ABC, abstractmethod

from dataportal.ingest.constants import BATCH_SIZE
from dataportal.ingest.es_repo import bulk_exec


class Flow(ABC):
    def __init__(self, index_name: str = "feature_index"):
        self.index = index_name
        self.buffer = []

    @abstractmethod
    def run(self, *args, **kwargs):
        ...

    def add(self, action):
        self.buffer.append(action)
        if len(self.buffer) >= BATCH_SIZE:
            self.flush()

    def flush(self):
        if not self.buffer:
            return
        bulk_exec(self.buffer)
        self.buffer.clear()