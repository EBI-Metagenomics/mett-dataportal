from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from dataportal.ingest.ppi.parsing import iter_ppi_rows
from dataportal.models import ProteinProteinDocument
from dataportal.ingest.es_repo import PPIIndexRepository

# --- helpers (reuse exact logic from your model for determinism) ---
def canonical_pair(a: str, b: str) -> Tuple[str, str]:
    return tuple(sorted([a, b]))

def build_pair_id(species_key: str, a: str, b: str) -> str:
    aa, bb = canonical_pair(a, b)
    return f"{species_key}:{aa}__{bb}"

def _species_key(species_name: Optional[str], species_map: Dict[str, str]) -> str:
    # Try configured acronym map, fallback to a slug from the species string.
    if species_name and species_name in species_map:
        return species_map[species_name]
    # fallback: first letters of genus+species, e.g. "Bacteroides uniformis" -> "BU"
    if species_name:
        parts = species_name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
    return "NA"

def _flags_and_rollups(doc: Dict) -> None:
    # convenience flags
    doc["has_xlms"] = bool(doc.get("xlms_peptides") or doc.get("xlms_files"))
    doc["has_string"] = doc.get("string_score") is not None
    doc["has_operon"] = doc.get("operon_score") is not None
    doc["has_ecocyc"] = doc.get("ecocyc_score") is not None
    doc["has_experimental"] = any(
        doc.get(k) is not None for k in [
            "melt_score","perturbation_score","abundance_score",
            "secondary_score","bayesian_score","tt_score","ds_score"
        ]
    )
    # evidence count
    numeric_keys = [
        "ds_score","tt_score","perturbation_score","abundance_score",
        "melt_score","secondary_score","bayesian_score",
        "string_score","operon_score","ecocyc_score",
    ]
    doc["evidence_count"] = sum(1 for k in numeric_keys if doc.get(k) is not None)

    # simple binning heuristic (tune later)
    s = doc.get("string_score")
    if (s is not None and s >= 0.7) or doc["evidence_count"] >= 4:
        doc["confidence_bin"] = "high"
    elif (s is not None and s >= 0.4) or doc["evidence_count"] >= 2:
        doc["confidence_bin"] = "medium"
    else:
        doc["confidence_bin"] = "low"

@dataclass
class PPICSVFlow:
    repo: PPIIndexRepository
    species_map: Dict[str, str]  # {"Bacteroides uniformis": "BU", ...}

    def run(self, folder: str, pattern: str = "*.csv", batch_size: int = 2000) -> int:
        """
        Sweep CSVs and bulk upsert into ppi_index.
        Returns number of docs indexed.
        """
        # Merge rows per canonical pair_id (across files), last-write-wins for numeric ties.
        merged: Dict[str, Dict] = {}

        for row in iter_ppi_rows(folder, pattern):
            sp_key = _species_key(row.get("species"), self.species_map)
            a, b = row["protein_a"], row["protein_b"]
            if not a or not b:
                continue
            aa, bb = canonical_pair(a, b)
            pair_id = build_pair_id(sp_key, aa, bb)

            base = merged.get(pair_id, {
                "pair_id": pair_id,
                "species_scientific_name": row.get("species"),
                "species_acronym": sp_key,
                "protein_a": aa,
                "protein_b": bb,
                "participants": [a, b],
                "participants_sorted": [aa, bb],
                "is_self_interaction": (aa == bb),
                # scores/evidence initialized None
                "ds_score": None, "tt_score": None, "perturbation_score": None,
                "abundance_score": None, "melt_score": None, "secondary_score": None,
                "bayesian_score": None, "string_score": None, "operon_score": None,
                "ecocyc_score": None, "xlms_peptides": None, "xlms_files": None,
                # optional experimental fields
                "experimental_condition_id": None, "experimental_condition": None,
            })

            # simple overwrite-if-not-None policy (you can swap to max/mean later)
            for k in ["ds_score","tt_score","perturbation_score","abundance_score",
                      "melt_score","secondary_score","bayesian_score",
                      "string_score","operon_score","ecocyc_score"]:
                v = row.get(k)
                if v is not None:
                    base[k] = v

            # text/list fields: prefer non-empty
            if row.get("xlms_peptides"):
                base["xlms_peptides"] = row["xlms_peptides"]
            if row.get("xlms_files"):
                base["xlms_files"] = row["xlms_files"]

            merged[pair_id] = base

        # compute flags/rollups and bulk
        actions = []
        for pair_id, doc in merged.items():
            _flags_and_rollups(doc)
            actions.append({
                "_op_type": "index",        # idempotent upsert
                "_index": self.repo.index_name,
                "_id": pair_id,
                "_source": doc,
            })

        return self.repo.bulk_index(actions, chunk_size=batch_size, refresh="wait_for")
