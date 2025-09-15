from __future__ import annotations

"""
Upsert-only importers for strain drug data.

- Uses StrainResolver to canonicalize incoming strain names to a single _id
  (prevents creating variant-docs like BU_CLAAAH218 vs BU_CLA_AA_H218).
- MIC import does NOT set a 'unit' field (per request).
- Metabolism import does NOT compute 'is_significant' (per request).
- Dedup is performed per array to keep documents idempotent across runs.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from dataportal.models import StrainDocument
from dataportal.ingest.es_repo import StrainIndexRepository
from dataportal.ingest.strain.parsers import iter_mic_rows, iter_metabolism_rows
from dataportal.ingest.strain.resolver import StrainResolver, isolate_lookup_key


class BaseImporter:
    def run(self) -> None:
        raise NotImplementedError


# ---------------------------
# Drug MIC (growth inhibition)
# ---------------------------

@dataclass
class DrugMICUpserter(BaseImporter):
    """
    Upserts MIC measurements into StrainDocument.drug_mic (nested array).

    Expected CSV columns (case-insensitive):
      - Strain
      - Drug
      - relation
      - drug_conc_um

    Notes:
      - 'unit' is intentionally omitted (not present in source).
      - Resolver is mandatory to avoid creating variant IDs.
    """
    repo: StrainIndexRepository
    resolver: StrainResolver
    bu_csv: Optional[str] = None
    pv_csv: Optional[str] = None

    @staticmethod
    def _dedup(existing: List[dict], new_items: List[dict]) -> List[dict]:
        """
        De-duplicate on a pragmatic key: (drug_name.lower, relation, mic_value rounded).
        """

        def key(it: dict):
            return (
                (it.get("drug_name") or "").lower(),
                it.get("relation"),
                round((it.get("mic_value") or 0.0), 6),
            )

        seen, out = set(), []
        # keep original order: existing first, then new additions
        for it in (existing or []) + (new_items or []):
            k = key(it)
            if k not in seen:
                seen.add(k)
                out.append(it)
        return out

    def run(self) -> None:
        # Group incoming rows by canonical strain id (resolved once)
        grouped: Dict[str, List[dict]] = {}
        for strain, payload in iter_mic_rows([self.bu_csv, self.pv_csv]):
            canonical_id = self.resolver.canonicalize_if_known(strain)
            if not canonical_id:
                # skip rows where strain is unknown
                continue
            grouped.setdefault(canonical_id, []).append(payload)

        for cid, items in grouped.items():
            doc = self.repo.get(cid)
            if not doc:
                # This should not happen, since resolver only returns known isolates
                continue

            existing = list(getattr(doc, "drug_mic", []) or [])
            doc.drug_mic = self._dedup(existing, items)
            self.repo.save(doc)


# ------------------------
# Drug Metabolism (SP5)
# ------------------------

@dataclass
class DrugMetabolismUpserter(BaseImporter):
    """
    Upserts metabolism measurements into StrainDocument.drug_metabolism (nested array).

    Expected CSV columns (case-insensitive):
      - Strain
      - Drug
      - DEGR_PERC
      - PVAL
      - PFDR
      - Metabolizer (optional)

    Notes:
      - No 'is_significant' computation here (left absent/blank).
      - Resolver is mandatory to avoid creating variant IDs.
    """
    repo: StrainIndexRepository
    resolver: StrainResolver
    bu_csv: Optional[str] = None
    pv_csv: Optional[str] = None

    @staticmethod
    def _dedup(existing: List[dict], new_items: List[dict]) -> List[dict]:
        """
        De-duplicate on (drug_name.lower, degr_percent, pval, fdr, metabolizer.lower).
        """

        def nf(x):  # normalized float
            return None if x is None else round(float(x), 6)

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
            doc = self.repo.get(cid)
            if not doc:
                continue

            existing = list(getattr(doc, "drug_metabolism", []) or [])
            doc.drug_metabolism = self._dedup(existing, items)
            self.repo.save(doc)
