from __future__ import annotations
from typing import Optional

SPECIES_NAME_BY_ACRONYM = {
    "BU": "Bacteroides uniformis",
    "PV": "Phocaeicola vulgatus",
}

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
