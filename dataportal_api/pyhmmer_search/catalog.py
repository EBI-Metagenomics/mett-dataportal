"""Species list for the protein search form, built from the strain index.

The search still reads the protein FASTA and ``members.sqlite``. This module
only fills the form: one row per species that has an enabled strain.
"""

from __future__ import annotations

from .constants import (
    COLLECTION_EXTENDED,
    COLLECTION_HD,
    DATABASE_ID,
    DATABASE_LABEL,
    HD_SPECIES,
    SHORTCUT_ALL_ID,
    SHORTCUT_ALL_LABEL,
    SHORTCUT_HD_ID,
    SHORTCUT_HD_LABEL,
)


def _strain_visible(enabled) -> bool:
    """Missing ``enabled`` stays visible. Only an explicit false hides a strain."""
    return enabled is not False


def build_catalog(rows: list[dict]) -> dict:
    """Group strain rows into the catalog the search form expects."""
    grouped: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict) or not _strain_visible(row.get("enabled")):
            continue
        acronym = str(row.get("species_acronym") or "").strip().upper()
        isolate = str(row.get("isolate_name") or "").strip()
        if not acronym or not isolate:
            continue
        entry = grouped.setdefault(
            acronym, {"names": {}, "isolates": set(), "type_strain": ""}
        )
        name = str(row.get("species_scientific_name") or "").strip()
        if name:
            entry["names"][name] = entry["names"].get(name, 0) + 1
        entry["isolates"].add(isolate)
        if row.get("type_strain") is True:
            current = entry["type_strain"]
            if not current or isolate < current:
                entry["type_strain"] = isolate

    species = []
    for acronym in sorted(grouped):
        entry = grouped[acronym]
        names = entry["names"]
        species.append(
            {
                "acronym": acronym,
                "name": max(names, key=names.get) if names else acronym,
                "isolates": len(entry["isolates"]),
                "type_strain": entry["type_strain"],
                "collection": (
                    COLLECTION_HD if acronym in HD_SPECIES else COLLECTION_EXTENDED
                ),
            }
        )

    shortcuts = [{"id": SHORTCUT_ALL_ID, "label": SHORTCUT_ALL_LABEL, "species": []}]
    hd = [acronym for acronym in HD_SPECIES if acronym in grouped]
    if hd:
        shortcuts.append(
            {"id": SHORTCUT_HD_ID, "label": SHORTCUT_HD_LABEL, "species": hd}
        )
    return {
        "id": DATABASE_ID,
        "name": DATABASE_LABEL,
        "shortcuts": shortcuts,
        "species": species,
    }


def load_strain_rows() -> list[dict]:
    """Enabled and disabled strains from the strain index. Grouping drops the hidden ones."""
    from dataportal.elasticsearch.resolver import resolve_read_index
    from dataportal.models.strains import StrainDocument

    search = StrainDocument.search(index=resolve_read_index("strains")).source(
        [
            "species_acronym",
            "species_scientific_name",
            "isolate_name",
            "type_strain",
            "enabled",
        ]
    )
    rows = []
    for hit in search.scan():
        rows.append(
            {
                "species_acronym": getattr(hit, "species_acronym", "") or "",
                "species_scientific_name": getattr(hit, "species_scientific_name", "")
                or "",
                "isolate_name": getattr(hit, "isolate_name", "") or "",
                "type_strain": getattr(hit, "type_strain", None),
                "enabled": getattr(hit, "enabled", None),
            }
        )
    return rows


def load_catalog() -> dict:
    return build_catalog(load_strain_rows())
