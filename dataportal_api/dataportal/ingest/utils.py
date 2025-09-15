from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

import pandas as pd

SPECIES_NAME_BY_ACRONYM = {
    "BU": "Bacteroides uniformis",
    "PV": "Phocaeicola vulgatus",
}


def list_csv_files(pathlike: str | None, exts=(".csv", ".tsv", ".tab", ".txt"), recursive=True) -> list[str]:
    if not pathlike: return []
    p = Path(pathlike).expanduser().resolve()
    if not p.exists(): print(f"[import_operons] not found: {p}"); return []
    if p.is_file() and p.suffix.lower() in exts: return [str(p)]
    if p.is_dir():
        globber = p.rglob if recursive else p.glob
        return [str(f) for f in sorted(globber("*")) if f.suffix.lower() in exts]
    return []


def normalize_strain_id(s: str) -> str:
    """Normalize strain ids like BU_H1-6 -> BU_H1_6."""
    if not s:
        return s
    s = s.strip()
    if "_" in s:
        head, tail = s.split("_", 1)
        return f"{head}_{tail.replace('-', '_')}"
    return s.replace("-", "_")


def strain_prefix(isolate_name: str) -> Optional[str]:
    return isolate_name.split("_", 1)[0] if "_" in isolate_name else None


def species_name_for_isolate(isolate_name: str) -> Optional[str]:
    acr = strain_prefix(isolate_name)
    return SPECIES_NAME_BY_ACRONYM.get(acr)


def canonical_ig_id_from_neighbors(left: str | None, right: str | None) -> str | None:
    left = (left or "").strip()
    right = (right or "").strip()
    if not left or not right:
        return None
    a, b = sorted([left, right])
    return f"IG:{a}__{b}"


def parse_dbxref(dbxref_string):
    if not dbxref_string or not dbxref_string.strip():
        return [], None, None
    parsed, uniprot_id, cog_id = [], None, None
    for entry in dbxref_string.split(","):
        parts = entry.split(":", 1)
        if len(parts) != 2:
            continue
        db, ref = parts
        parsed.append({"db": db, "ref": ref})
        if db == "UniProt":
            uniprot_id = ref
        elif db == "COG":
            cog_id = ref
    return parsed, uniprot_id, cog_id


def parse_ig_neighbors(feature_id: str):
    # Expect: IG-between-<A>-and-<B>
    try:
        core = feature_id.split("IG-between-")[1]
        left, right = core.split("-and-")
        return left, right
    except Exception:
        return None, None


def read_tsv_mapping(path, key_col, val_col, strip_suffix=".fa"):
    mapping = {}
    with open(path, "r") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            v = row[val_col]
            if strip_suffix and v.endswith(strip_suffix):
                v = v[: -len(strip_suffix)]
            mapping[row[key_col]] = v
    return mapping


def pick(d: dict, *keys, default=None):
    """Return first non-empty key value from dict."""
    for k in keys:
        if k in d and d[k] not in (None, "", []):
            return d[k]
    return default


def chunks_from_table(path: str, chunksize: int = 10_000):
    suffix = Path(path).suffix.lower()
    sep = "," if suffix == ".csv" else "\t"

    defaults = dict(
        sep=sep,
        chunksize=chunksize,
        engine="python",
        on_bad_lines="skip",
        dtype=str,
        encoding_errors="replace"
    )
    return pd.read_csv(path, **defaults)


def canonical_pair_id(a: str, b: str) -> str:
    """Order-insensitive pair id."""
    a = (a or "").strip();
    b = (b or "").strip()
    x, y = sorted([a, b])
    return f"{x}__{y}"
