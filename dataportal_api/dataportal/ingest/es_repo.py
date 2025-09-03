from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from elasticsearch import NotFoundError
from dataportal.models import StrainDocument

@dataclass
class StrainIndexRepository:
    """Read/write StrainDocument to a specific concrete ES index."""
    concrete_index: str

    def get(self, isolate_name: str) -> Optional[StrainDocument]:
        try:
            return StrainDocument.get(id=isolate_name, index=self.concrete_index, ignore=404)
        except NotFoundError:
            return None

    def save(self, doc: StrainDocument) -> None:
        doc.save(index=self.concrete_index)
