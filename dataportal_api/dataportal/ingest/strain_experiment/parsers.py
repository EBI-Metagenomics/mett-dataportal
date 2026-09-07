from __future__ import annotations

import os
from typing import Iterable, List, Optional, Tuple

import pandas as pd


def _safe_float(x) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return None


def iter_mic_rows(csv_paths: List[str], default_unit: str = "uM") -> Iterable[Tuple[str, dict]]:
    """Yields (strain, payload) from MIC CSVs: Strain, Drug, relation, drug_conc_um."""
    del default_unit  # unit is not stored on MIC docs
    for p in csv_paths:
        if not p or not os.path.exists(p):
            continue
        df = pd.read_csv(p)
        cols = {c.lower(): c for c in df.columns}
        for _, row in df.iterrows():
            yield str(row[cols.get("strain", "Strain")]).strip(), {
                "drug_name": str(row[cols.get("drug", "Drug")]).strip(),
                "relation": str(row[cols.get("relation", "relation")]).strip(),
                "mic_value": _safe_float(row[cols.get("drug_conc_um", "drug_conc_um")]),
            }


def iter_metabolism_rows(csv_paths: List[str]) -> Iterable[Tuple[str, dict]]:
    """Yields (strain, payload) from metabolism CSVs."""
    for p in csv_paths:
        if not p or not os.path.exists(p):
            continue
        df = pd.read_csv(p)
        cols = {c.lower(): c for c in df.columns}
        for _, row in df.iterrows():
            yield str(row[cols.get("strain", "Strain")]).strip(), {
                "drug_name": str(row[cols.get("drug", "Drug")]).strip(),
                "degr_percent": _safe_float(row[cols.get("degr_perc", "DEGR_PERC")]),
                "pval": _safe_float(row[cols.get("pval", "PVAL")]),
                "fdr": _safe_float(row[cols.get("pfdr", "PFDR")]),
                "metabolizer_classification": (
                    str(row[cols.get("metabolizer", "Metabolizer")]).strip()
                    if (cols.get("metabolizer") or "Metabolizer" in df.columns)
                    else None
                ),
            }
