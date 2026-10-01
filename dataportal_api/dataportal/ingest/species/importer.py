from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
from elasticsearch.helpers import bulk

from dataportal.ingest.utils import reset_species_name_cache


def parse_enabled_flag(value: Any, default: bool = True) -> bool:
    """Parse CSV/TSV enabled values. Strings like 'false' must not become True."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return default


def load_species_rows(csv_path: str) -> pd.DataFrame:
    species_df = pd.read_csv(
        csv_path,
        dtype={"scientific_name": "string", "common_name": "string", "acronym": "string"},
    )
    if "taxonomy_id" in species_df.columns:
        species_df["taxonomy_id"] = pd.to_numeric(
            species_df["taxonomy_id"], errors="coerce"
        ).astype("Int64")
    if "enabled" in species_df.columns:
        species_df["enabled"] = species_df["enabled"].map(parse_enabled_flag)
    else:
        species_df["enabled"] = True
    for col in ("scientific_name", "common_name", "acronym"):
        if col in species_df.columns:
            species_df[col] = species_df[col].fillna("").str.strip()
    return species_df


def iter_species_actions(species_df: pd.DataFrame, index_name: str):
    for row in species_df.itertuples(index=False):
        src: Dict[str, Any] = {
            "scientific_name": getattr(row, "scientific_name", "") or "",
            "common_name": getattr(row, "common_name", "") or "",
            "acronym": getattr(row, "acronym", "") or "",
        }
        tax = getattr(row, "taxonomy_id", None)
        if tax is not None and pd.notna(tax):
            src["taxonomy_id"] = int(tax)

        src["enabled"] = parse_enabled_flag(getattr(row, "enabled", True))

        yield {
            "_op_type": "index",
            "_index": index_name,
            "_id": src["acronym"] or None,
            "_source": src,
        }


def ingest_species(
    client,
    csv_path: str,
    index_name: str,
    *,
    refresh: bool = False,
) -> tuple[int, Optional[list], int]:
    species_df = load_species_rows(csv_path)
    ok, errors = bulk(
        client,
        iter_species_actions(species_df, index_name),
        chunk_size=2000,
        request_timeout=120,
        refresh="wait_for" if refresh else False,
    )
    reset_species_name_cache()
    try:
        from dataportal.utils.species_registry import invalidate_cache

        invalidate_cache()
    except Exception:
        pass
    return ok, errors if errors else None, len(species_df)
