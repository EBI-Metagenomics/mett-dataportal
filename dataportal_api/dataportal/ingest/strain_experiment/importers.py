from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from dataportal.models import StrainExperimentDocument
from dataportal.ingest.es_repo import StrainExperimentIndexRepository, StrainIndexRepository
from dataportal.ingest.strain_experiment.parsers import iter_mic_rows, iter_metabolism_rows
from dataportal.ingest.strain.resolver import StrainResolver

"""
Upsert-only importers for strain drug data into strain_experiment_index.

- Uses StrainResolver (against strain_index) to canonicalize isolate names.
- MIC import does NOT set a 'unit' field (per request).
- Metabolism import does NOT compute 'is_significant' (per request).
"""


class BaseImporter:
    def run(self) -> None:
        raise NotImplementedError


def _ensure_experiment_doc(
    experiment_repo: StrainExperimentIndexRepository,
    strain_repo: Optional[StrainIndexRepository],
    isolate_id: str,
) -> Optional[StrainExperimentDocument]:
    doc = experiment_repo.get(isolate_id)
    if doc:
        return doc
    species_acronym = None
    species_scientific_name = None
    if strain_repo:
        strain = strain_repo.get(isolate_id)
        if strain:
            species_acronym = getattr(strain, "species_acronym", None)
            species_scientific_name = getattr(strain, "species_scientific_name", None)
    doc = StrainExperimentDocument(
        isolate_name=isolate_id,
        species_acronym=species_acronym,
        species_scientific_name=species_scientific_name,
    )
    doc.meta.id = isolate_id
    return doc


@dataclass
class DrugMICUpserter(BaseImporter):
    """Upserts MIC measurements into StrainExperimentDocument.drug_mic."""

    repo: StrainExperimentIndexRepository
    resolver: StrainResolver
    strain_repo: Optional[StrainIndexRepository] = None
    bu_csv: Optional[str] = None
    pv_csv: Optional[str] = None

    @staticmethod
    def _dedup(existing: List[dict], new_items: List[dict]) -> List[dict]:
        def key(it: dict):
            return (
                (it.get("drug_name") or "").lower(),
                it.get("relation"),
                round((it.get("mic_value") or 0.0), 6),
            )

        seen, out = set(), []
        for it in (existing or []) + (new_items or []):
            k = key(it)
            if k not in seen:
                seen.add(k)
                out.append(it)
        return out

    def run(self) -> None:
        grouped: Dict[str, List[dict]] = {}
        for strain, payload in iter_mic_rows([self.bu_csv, self.pv_csv]):
            canonical_id = self.resolver.canonicalize_if_known(strain)
            if not canonical_id:
                continue
            grouped.setdefault(canonical_id, []).append(payload)

        for cid, items in grouped.items():
            doc = _ensure_experiment_doc(self.repo, self.strain_repo, cid)
            if not doc:
                continue
            existing = list(getattr(doc, "drug_mic", []) or [])
            doc.drug_mic = self._dedup(existing, items)
            self.repo.save(doc)


@dataclass
class DrugMetabolismUpserter(BaseImporter):
    """Upserts metabolism measurements into StrainExperimentDocument.drug_metabolism."""

    repo: StrainExperimentIndexRepository
    resolver: StrainResolver
    strain_repo: Optional[StrainIndexRepository] = None
    bu_csv: Optional[str] = None
    pv_csv: Optional[str] = None

    @staticmethod
    def _dedup(existing: List[dict], new_items: List[dict]) -> List[dict]:
        def nf(x):
            return None if x is None else round(float(x), 6)

        def key(it: dict):
            return (
                (it.get("drug_name") or "").lower(),
                nf(it.get("degr_percent")),
                nf(it.get("pval")),
                nf(it.get("fdr")),
                (
                    (it.get("metabolizer_classification") or "").lower()
                    if it.get("metabolizer_classification")
                    else ""
                ),
            )

        seen, out = set(), []
        for it in (existing or []) + (new_items or []):
            k = key(it)
            if k not in seen:
                seen.add(k)
                out.append(it)
        return out

    def run(self) -> None:
        grouped: Dict[str, List[dict]] = {}
        for strain, payload in iter_metabolism_rows([self.bu_csv, self.pv_csv]):
            canonical_id = self.resolver.canonicalize_if_known(strain)
            if not canonical_id:
                continue
            grouped.setdefault(canonical_id, []).append(payload)

        for cid, items in grouped.items():
            doc = _ensure_experiment_doc(self.repo, self.strain_repo, cid)
            if not doc:
                continue
            existing = list(getattr(doc, "drug_metabolism", []) or [])
            doc.drug_metabolism = self._dedup(existing, items)
            self.repo.save(doc)
