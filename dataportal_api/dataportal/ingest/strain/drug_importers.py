from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

from dataportal.models import StrainDocument
from dataportal.ingest.es_repo import StrainIndexRepository
from dataportal.ingest.utils import normalize_strain_id
from .parsers import iter_mic_rows, iter_metabolism_rows

class BaseImporter:
    def run(self) -> None:
        raise NotImplementedError

# -------- MIC upsert --------
@dataclass
class DrugMICUpserter(BaseImporter):
    repo: StrainIndexRepository
    bu_csv: Optional[str] = None
    pv_csv: Optional[str] = None
    default_unit: str = "uM"

    @staticmethod
    def _dedup(existing: List[dict], new_items: List[dict]) -> List[dict]:
        def key(it: dict):
            return (
                (it.get("drug_name") or "").lower(),
                it.get("relation"),
                round((it.get("mic_value") or 0.0), 6),
                (it.get("unit") or "").lower(),
            )
        seen, out = set(), []
        for it in (existing or []) + new_items:
            k = key(it)
            if k not in seen:
                seen.add(k)
                out.append(it)
        return out

    def run(self) -> None:
        by_strain: Dict[str, List[dict]] = {}
        for strain, payload in iter_mic_rows([self.bu_csv, self.pv_csv], default_unit=self.default_unit):
            strain = normalize_strain_id(strain)
            by_strain.setdefault(strain, []).append(payload)

        for strain, items in by_strain.items():
            doc = self.repo.get(strain)
            if doc is None:
                # create minimal skeleton; do NOT touch type_strain or other fields
                doc = StrainDocument(meta={"id": strain}, strain_id=strain, isolate_name=strain)
            existing = list(getattr(doc, "drug_mic", []) or [])
            doc.drug_mic = self._dedup(existing, items)
            self.repo.save(doc)

# -------- Metabolism upsert --------
@dataclass
class DrugMetabolismUpserter(BaseImporter):
    repo: StrainIndexRepository
    bu_csv: Optional[str] = None
    pv_csv: Optional[str] = None

    @staticmethod
    def _dedup(existing: List[dict], new_items: List[dict]) -> List[dict]:
        def nf(x): return None if x is None else round(float(x), 6)
        def key(it: dict):
            return (
                (it.get("drug_name") or "").lower(),
                nf(it.get("degr_percent")),
                nf(it.get("pval")),
                nf(it.get("fdr")),
                (it.get("metabolizer_classification") or "").lower()
                    if it.get("metabolizer_classification") else "",
            )
        seen, out = set(), []
        for it in (existing or []) + new_items:
            k = key(it)
            if k not in seen:
                seen.add(k)
                out.append(it)
        return out

    def run(self) -> None:
        by_strain: Dict[str, List[dict]] = {}
        for strain, payload in iter_metabolism_rows([self.bu_csv, self.pv_csv]):
            strain = normalize_strain_id(strain)
            # NOTE: no is_significant computation
            by_strain.setdefault(strain, []).append(payload)

        for strain, items in by_strain.items():
            doc = self.repo.get(strain)
            if doc is None:
                doc = StrainDocument(meta={"id": strain}, strain_id=strain, isolate_name=strain)
            existing = list(getattr(doc, "drug_metabolism", []) or [])
            doc.drug_metabolism = self._dedup(existing, items)
            self.repo.save(doc)
