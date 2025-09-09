from __future__ import annotations
import csv, glob, os
from typing import Dict, Iterable, Iterator, List, Optional

PPI_CSV_COLUMNS = [
    "species","id","protein_a","protein_b","ds_score","tt_score","perturb_score",
    "gp_score","melt_score","sec_score","bn_score","string_physical_score",
    "operon_score","ecocyc_score","xlms_peptides","xlms_files",
]

def _flt(v: Optional[str]) -> Optional[float]:
    if v is None:
        return None
    v = str(v).strip()
    if not v or v.lower() in {"na", "nan", "none"}:
        return None
    try:
        return float(v)
    except Exception:
        return None

def _split_list(v: Optional[str]) -> Optional[List[str]]:
    if not v:
        return None
    parts = [p.strip() for p in str(v).split(",")]
    parts = [p for p in parts if p]
    return parts or None

def iter_ppi_rows(folder: str, pattern: str = "*.csv") -> Iterator[Dict]:
    """Yield raw rows from all CSVs in `folder` matching pattern."""
    for path in sorted(glob.glob(os.path.join(folder, pattern))):
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # optional: verify header superset
            missing = set(["species","protein_a","protein_b"]) - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"PPI CSV missing columns {missing} in {path}")
            for row in reader:
                yield {
                    "species": row.get("species"),
                    "csv_id": row.get("id"),  # may be None; not trusted for canonicalization
                    "protein_a": row.get("protein_a"),
                    "protein_b": row.get("protein_b"),
                    "ds_score": _flt(row.get("ds_score")),
                    "tt_score": _flt(row.get("tt_score")),
                    "perturbation_score": _flt(row.get("perturb_score")),
                    "abundance_score": _flt(row.get("gp_score")),
                    "melt_score": _flt(row.get("melt_score")),
                    "secondary_score": _flt(row.get("sec_score")),
                    "bayesian_score": _flt(row.get("bn_score")),
                    "string_score": _flt(row.get("string_physical_score")),
                    "operon_score": _flt(row.get("operon_score")),
                    "ecocyc_score": _flt(row.get("ecocyc_score")),
                    "xlms_peptides": (row.get("xlms_peptides") or None),
                    "xlms_files": _split_list(row.get("xlms_files")),
                }
